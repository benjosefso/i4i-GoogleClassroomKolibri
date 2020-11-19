from __future__ import print_function
import pickle
import os.path
import logging, sys
import json
import io
import os
from slugify import slugify
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload

# Added logging for tracking errors
logging.basicConfig(filename='scrapper.log', level=logging.DEBUG)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
'https://www.googleapis.com/auth/classroom.coursework.students',
'https://www.googleapis.com/auth/classroom.topics.readonly',
'https://www.googleapis.com/auth/drive.readonly',
'https://www.googleapis.com/auth/drive.file']

"""
    Google Classroom Scraper by Ben Josefson
    Script utilitzing Google Classroom API to scrape data from a Google Classroom Course

    Also downloads and converts documents to pdf from Google Drive

    Access to a google account and permissions to access certain Google Classroom Data
    must be granted.

    10/11/2020
"""

#Mime-Type lists for handling of different versions
ppMime = {"application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.template",
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
            "application/vnd.ms-powerpoint.addin.macroEnabled.12",
            "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
            "application/vnd.ms-powerpoint.template.macroEnabled.12",
            "application/vnd.ms-powerpoint.slideshow.macroEnabled.12"
}
docMime = {"application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
            "application/vnd.ms-word.document.macroEnabled.12",
            "application/vnd.ms-word.template.macroEnabled.12",
            "text/plain"
}
exMime = {"application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
            "application/vnd.ms-excel.sheet.macroEnabled.12",
            "application/vnd.ms-excel.template.macroEnabled.12",
            "application/vnd.ms-excel.addin.macroEnabled.12",
            "application/vnd.ms-excel.sheet.binary.macroEnabled.12"
}
imgMime = {"image/bmp", "image/gif", "image/jpeg", "image/vnd.microsoft.icon",
            "image/png", "image/svg+xml", "image/ttf", "image/webp"
}
gooMime = {"application/vnd.google-apps.document",
            "application/vnd.google-apps.presentation",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.drawing",
            "application/vnd.google-apps.file"
}
pdfMime = {"application/pdf",
            "application/x-pdf"
}

#Document extentions to google extensions
extensions = {"docx" : "document",
                "pptx" : "presentation",
                "xlsx" : "spreadsheet",
                "png"  : "drawing",
                "pdf" : "file"
}

def doc_convert(file_id, file_name, service):
    converted = service.files().export_media(fileId=file_id,mimeType='application/pdf')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, converted)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    with open("documents/" + file_name + ".pdf",'wb') as out:
        out.write(fh.getvalue())


def doc_googlfy(ext, file_id, service):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    with open("documents/tempdoc." + ext,'wb') as out:
        out.write(fh.getvalue())

    file_metadata = {
        'name': 'Temp File',
        'mimeType': 'application/vnd.google-apps.' + extensions[ext]
    }
    media = MediaFileUpload("documents/tempdoc." + ext, resumable=True)
    convertFile = service.files().create(body=file_metadata,media_body=media,fields='id').execute()
    file_id = convertFile['id']
    return file_id

def doc_default(file_id, file_name, service):
    converted = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, converted)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    with open("documents/" + file_name + ".pdf",'wb') as out:
        out.write(fh.getvalue())

#Create Comprehensive Course Class to be converted to json
class CompleteCourse:
    def __init__(self,course):
        self.course = course


    courseTopics = {}
    courseAssignments = {}

#Define custom encoding for this class to JSON
def encode_CompleteCourse(x):
    if isinstance(x, CompleteCourse):
        return { "Course" : x.course, "Topics" : x.courseTopics, "Assignments" : x.courseAssignments}
    else:
        type_name = z.__class__.__name__
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)
    service2 = build('drive', 'v3', credentials=creds)


    # Call the Classroom API
    results = service.courses().list(pageSize=10).execute()
    courses = results.get('courses', [])

    if not courses:
        print('No courses found.')
    else:
        print('Courses:')
        i = 1
        for course in courses:
            print(str(i)+' '+course['name'])
            i+=1

        print("Select a course:")
        inputcoursenum= int(input()) -1
        selectedCourse = courses[inputcoursenum]
        selectedCourseId = selectedCourse["id"]

        #Creation of Completed Course Object to be passed to JSON with GC Course object
        thisCourse = CompleteCourse(selectedCourse)

        #Retrieve list of topics
        results = service.courses().topics().list(courseId=selectedCourseId).execute()
        topicslist = results.get('topic', [])

        logging.debug(topicslist)

        if not topicslist:
                print('No topics found.')
        else:
                for topic in topicslist:
                    #Store topic data
                    thisCourse.courseTopics[topic['name']] = topic

        #Retrieve list of coursework
        results = service.courses().courseWorkMaterials().list(courseId=selectedCourseId).execute()
        courseworksmaterial = results.get('courseWorkMaterial', [])

        logging.debug(courseworksmaterial)

        if not courseworksmaterial:
            print('No coursework found.')
        else:

            for courseWork in courseworksmaterial:
                #Store coursework data
                thisCourse.courseAssignments[courseWork["title"]]=courseWork

                #Check for driveFiles to be downloaded
                if "materials" in thisCourse.courseAssignments[courseWork["title"]]:
                    for spec_mat in thisCourse.courseAssignments[courseWork["title"]]["materials"]:
                        if "driveFile" in spec_mat:
                            file_name = slugify(spec_mat["driveFile"]["driveFile"]["title"])
                            file_id = spec_mat["driveFile"]["driveFile"]["id"]
                            file = service2.files().get(fileId=file_id).execute()
                            print(file["mimeType"])

                            #WORD DOCUMENT
                            if file["mimeType"] in docMime:
                                googId=doc_googlfy("docx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #POWERPOINT PRESENTATION
                            elif file["mimeType"] in ppMime:
                                googId=doc_googlfy("pptx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #EXCEL DOCUMENT
                            elif file["mimeType"] in exMime:
                                googId=doc_googlfy("xlsx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #IMAGE
                            elif file["mimeType"] in imgMime:
                                googId=doc_googlfy("png", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #PDF
                            elif file["mimeType"] in pdfMime:
                                    doc_default(file_id,file_name,service2)

                            #ALREADY GOOGLE FORMAT
                            elif file["mimeType"] in gooMime:
                                doc_convert(file_id, file_name, service2)

                            else:
                                print("File type not recognized.")

        results = service.courses().courseWork().list(courseId=selectedCourseId).execute()
        courseworks = results.get('courseWork', [])

        logging.debug(courseworks)

        if not courseworks:
            print('No coursework found.')
        else:

            for courseWork in courseworks:
                #Store coursework data
                thisCourse.courseAssignments[courseWork["title"]]=courseWork

                #Check for driveFiles to be downloaded
                if "materials" in thisCourse.courseAssignments[courseWork["title"]]:
                    for spec_mat in thisCourse.courseAssignments[courseWork["title"]]["materials"]:
                        if "driveFile" in spec_mat:
                            file_name = slugify(spec_mat["driveFile"]["driveFile"]["title"])
                            file_id = spec_mat["driveFile"]["driveFile"]["id"]
                            file = service2.files().get(fileId=file_id).execute()
                            print(file["mimeType"])

                            #WORD DOCUMENT
                            if file["mimeType"] in docMime:
                                googId=doc_googlfy("docx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #POWERPOINT PRESENTATION
                            elif file["mimeType"] in ppMime:
                                googId=doc_googlfy("pptx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #EXCEL DOCUMENT
                            elif file["mimeType"] in exMime:
                                googId=doc_googlfy("xlsx", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #IMAGE
                            elif file["mimeType"] in imgMime:
                                googId=doc_googlfy("png", file_id, service2)
                                doc_convert(googId,file_name, service2)
                                service2.files().delete(fileId=googId).execute()

                            #PDF
                            elif file["mimeType"] in pdfMime:
                                    googId=doc_googlfy("pdf", file_id, service2)
                                    doc_convert(googId,file_name, service2)
                                    service2.files().delete(fileId=googId).execute()

                            #ALREADY GOOGLE FORMAT
                            elif file["mimeType"] in gooMime:
                                doc_convert(file_id, file_name, service2)

                            else:
                                print("File type not recognized.")

    #Dump all course information to JSON file gc_data.json
    with open("gc_data.json", "w") as gc_data:
        json.dump(thisCourse,gc_data,indent=1,default=encode_CompleteCourse)


if __name__ == '__main__':
    main()

from __future__ import print_function
import pickle
import os.path
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
'https://www.googleapis.com/auth/classroom.coursework.students',
'https://www.googleapis.com/auth/classroom.topics.readonly']

"""
    Google Classroom Scraper by Ben Josefson 
    Script utilitzing Google Classroom API to scrape data from a Google Classroom Course
    
    Access to a google account and permissions to access certain Google Classroom Data
    must be granted.
    
    9/30/2020
    """

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

    # Call the Classroom API
    results = service.courses().list(pageSize=10).execute()
    courses = results.get('courses', [])

    # Open JSON Writer
    with open('gc_data.json', mode='w') as gc_data:

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

            if not topicslist:
                 print('No topics found.')
            else:
                 for topic in topicslist:
                     #Store topic data
                     thisCourse.courseTopics[topic['name']] = topic
                        
            #Retrieve list of coursework
            results = service.courses().courseWork().list(courseId=selectedCourseId).execute()
            courseworks = results.get('courseWork', [])

            if not courseworks:
                 print('No coursework found.')
            else:     
                 for courseWork in courseworks:
                     #Store coursework data
                     thisCourse.courseAssignments[courseWork['title']]=courseWork
                     
        #Dump all course information to JSON file gc_data.json
        json.dump(thisCourse,gc_data,indent=1,default=encode_CompleteCourse)
            

if __name__ == '__main__':
    main()

#!/usr/bin/env python
from le_utils.constants import licenses, exercises
from le_utils.constants.languages import getlang
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import DocumentNode, AudioNode, VideoNode, HTML5AppNode, TopicNode
from ricecooker.classes.files import DocumentFile, AudioFile, VideoFile, YouTubeVideoFile, YouTubeSubtitleFile, HTMLZipFile
from ricecooker.classes.licenses import get_license
import json
import requests
import copy
from slugify import slugify
#Web Scraper Libraries
from ricecooker.utils.html_writer import HTMLWriter
import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin

"""
   Kolibri Uploader by Ben Josefson, Collin Starr, and Meadow Walshaw-Wertz 
   10/21/2020
   Takes the json representation of a Google Classroom course and creates a Kolibri Channel with a similar structure.
   
   Currently does the following:
   1. Copys topics and topic data
   2. Copys assignments to their respective topics with metadata
   3. Downloads youtube videos attached to assignments
   4. Uploads documents
   5. Copy assignments not linked to a topic
   6. Download webpages/links
"""

def videoAssignment(material):
    video_node = VideoNode(
        source_id= material["youtubeVideo"]["id"],  # usually set source_id to youtube_id
        title=material["youtubeVideo"]["title"],
        license=get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
        language=getlang('en').id,
        derive_thumbnail=True,  # video-specicig flag
        thumbnail=None,
        files=[
                YouTubeVideoFile(youtube_id=material["youtubeVideo"]["id"], high_resolution=False, language='en'),
                YouTubeSubtitleFile(youtube_id=material["youtubeVideo"]["id"], language='en')
            ]
    )
    return video_node


def linkAssignment(material):
    url = material["link"]["url"]                        
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"                            
    html = session.get(url).content                         
    soup = bs(html, "html.parser")
        
    script_files = []
    css_files = []

    for script in soup.find_all("script"):
        if script.attrs.get("src"):
        # if the tag has the attribute 'src'
            script_url = urljoin(url, script.attrs.get("src"))
            script_files.append(script_url)

    for css in soup.find_all("link"):
        if css.attrs.get("href"):
            css_url = urljoin(url, css.attrs.get("href"))
            css_files.append(css_url)
                                            
    with HTMLWriter('./myzipper.zip') as zipper:                                    
        with open("index.html", "w", encoding = "utf-8") as f:
            index_content = soup.prettify()
            zipper.write_index_contents(index_content)
                                            
        with open("javascript_files.js") as f:
            for js_file in script_files:
                script_path = zipper.write_url(js_file, "scripts.js", directory = "src")
                script = "<script src='{}' type='text/javascript'></script>".format(script_path)
                                                
        with open("css_files.css", "w") as f:
            for css_file in css_files:
                print(css_file, file=f)
                css_path = zipper.write_url(css_file, "style.css", directory = "styles")
                extra_head = "<link href='{}' rel='stylesheet'></link>".format(css_path)
                                                                 
    link_file = HTMLZipFile(path = './myzipper.zip')
    link_node = HTML5AppNode(
        source_id = material["link"]["url"],
        title = material["link"]["title"],
        license = get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
        language = getlang('en').id,
        derive_thumbnail = False,
        thumbnail = None,
        files=[link_file]      
    )
    return link_node

def formAssignment(material):
    print("form")
    #TODO
    #return form_node

def documentAssignment(material):
    docPath = "documents/" + slugify(material["driveFile"]["driveFile"]["title"]) + ".pdf"

    document_node = DocumentNode(
        source_id=material["driveFile"]["driveFile"]["id"],
        title=material["driveFile"]["driveFile"]["title"],
        language=getlang('en').id,
        license=get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
        derive_thumbnail=True,
        thumbnail=None,
        files=[DocumentFile(
            path=str(docPath),
            language=getlang('en').id
        )]
    )
    print(courseDataCopy["Assignments"])
    return document_node

def addAssignment(a_info):
    try:
        assignment = TopicNode(
            title = a_info['title'],
            source_id = a_info['id'],
            description = a_info['description'],
            language='en',
            derive_thumbnail=True,
            thumbnail=None
        )
    except:
        assignment = TopicNode(
            title = a_info['title'], 
            source_id = a_info['id'],
            language='en',
            derive_thumbnail=True,
            thumbnail=None
        )
    return assignment


class MyChef(SushiChef):

    global courseData
    global courseDataCopy
    with open('gc_data.json', mode='r') as gc_data:
        courseData = json.load(gc_data)
        courseDataCopy = copy.deepcopy(courseData)

    #set general information for Kolibri Channel
    if 'description' in courseData['Course']:
        channel_info = {
            "CHANNEL_TITLE": courseData['Course']['name'],
            "CHANNEL_SOURCE_DOMAIN": "Google Classroom",
            "CHANNEL_SOURCE_ID": courseData['Course']['alternateLink'],
            "CHANNEL_LANGUAGE": "en",  # le_utils language code
            "CHANNEL_DESCRIPTION": courseData['Course']['description'],
        }
    else:
        channel_info = {
            "CHANNEL_TITLE": courseData['Course']['name'],
            "CHANNEL_SOURCE_DOMAIN": "Google Classroom",
            "CHANNEL_SOURCE_ID": courseData['Course']['alternateLink'],
            "CHANNEL_LANGUAGE": "en",  # le_utils language code
        }

    def construct_channel(self, **kwargs):
        channel = self.get_channel(**kwargs)

        #Create each topic node
        for t_id, t_info in courseData['Topics'].items():
            topic = TopicNode(
                title = t_info['name'], 
                source_id = t_info['topicId'],
                derive_thumbnail=True,
                thumbnail=None
            )
            channel.add_child(topic)

            #iterate through assignments and add them if they match the assingnment topic
            for a_id, a_info in courseData['Assignments'].items():
                if 'topicId' in a_info and a_info['topicId'] == t_info['topicId']:
                    assignment = addAssignment(a_info)
                    topic.add_child(assignment)

                    if "materials" in a_info:
                        #iterate through materials in the current assignment and add them if they match the material type
                        for spec_mat in a_info["materials"]:

                            if "youtubeVideo" in spec_mat: assignment.add_child(videoAssignment(spec_mat))

                            elif "link" in spec_mat: assignment.add_child(linkAssignment(spec_mat))
                                #Add this case with web scraping
                                
                            elif "form" in spec_mat: assignment.add_child(formAssignment(spec_mat))
                                #Might not add this case

                            elif "driveFile" in spec_mat: assignment.add_child(documentAssignment(spec_mat))

                elif 'topicId' not in a_info and a_id in courseDataCopy["Assignments"]:
                    assignment = addAssignment(a_info)
                    channel.add_child(assignment)

                    if "materials" in a_info:
                        for spec_mat in a_info["materials"]:

                            if "youtubeVideo" in spec_mat: assignment.add_child(videoAssignment(spec_mat))
                                

                            elif "link" in spec_mat: assignment.add_child(linkAssignment(spec_mat))
                                #Add this case with web scraping
                                
                            elif "form" in spec_mat: assignment.add_child(formAssignment(spec_mat))
                                #Might not add this case

                            elif "driveFile" in spec_mat: assignment.add_child(documentAssignment(spec_mat))

                    del courseDataCopy['Assignments'][a_id]
        return channel

        


if __name__ == "__main__":
    """
    Run this script on the command line using:
        python sushichef.py  --token=b4a40e441ab0f7dc98b34e16ada81fada6bc16d6 
        The token above is Ben's personal token, your own can be found on Kolibri studio at 
        https://studio.learningequality.org/settings/tokens
    """
    simple_chef = MyChef()
    simple_chef.main()

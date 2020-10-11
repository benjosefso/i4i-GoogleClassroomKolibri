#!/usr/bin/env python
from le_utils.constants import licenses, exercises
from le_utils.constants.languages import getlang
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import DocumentNode, AudioNode, VideoNode, HTML5AppNode, TopicNode
from ricecooker.classes.files import DocumentFile, AudioFile, VideoFile, YouTubeVideoFile, YouTubeSubtitleFile, HTMLZipFile
from ricecooker.classes.licenses import get_license
import json
import requests
from slugify import slugify

"""
   Kolibri Uploader by Ben Josefson 9/30/2020
   Takes the json representation of a Google Classroom course and creates a Kolibri Channel with a similar structure.
   
   Currently does the following:
   1. Copys topics and topic data
   2. Copys assignments to their respective topics with metadata
   3. Downloads youtube videos attached to assignments
   4. Uploads documents
   
   To Do:
   1. Copy assignments not linked to a topic
   2. Download webpages/links
"""

class MyChef(SushiChef):
    with open('gc_data.json', mode='r') as gc_data:
        global courseData
        courseData = json.load(gc_data)


        print(courseData)

        channel_info = {
            "CHANNEL_TITLE": courseData['Course']['name'],
            "CHANNEL_SOURCE_DOMAIN": courseData['Course']['name'],
            "CHANNEL_SOURCE_ID": courseData['Course']['alternateLink'],
            "CHANNEL_LANGUAGE": "en",  # le_utils language code
            "CHANNEL_THUMBNAIL": courseData['Course']['name'],
            "CHANNEL_DESCRIPTION": courseData['Course']['description'],
        }

        def construct_channel(self, **kwargs):
            channel = self.get_channel(**kwargs)

            for t_id, t_info in courseData['Topics'].items():
                topic = TopicNode(title = t_info['name'], source_id = t_info['topicId'])
                channel.add_child(topic)

                for a_id, a_info in courseData['Assignments'].items():
                    try:
                        assignment = TopicNode(title = a_info['title'], source_id = a_info['id'], description = a_info['description'])
                    except:
                        assignment = TopicNode(title = a_info['title'], source_id = a_info['id'])

                    if a_info['topicId'] == t_info['topicId']:
                        topic.add_child(assignment)

                        if "materials" in a_info:
                            for spec_mat in a_info["materials"]:

                                if "youtubeVideo" in spec_mat:
                                
                                    video_node = VideoNode(
                                        source_id= spec_mat["youtubeVideo"]["id"],  # usually set source_id to youtube_id
                                        title=spec_mat["youtubeVideo"]["title"],
                                        license=get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
                                        language=getlang('en').id,
                                        derive_thumbnail=True,  # video-specicig flag
                                        thumbnail=None,
                                        files=[
                                            YouTubeVideoFile(youtube_id=spec_mat["youtubeVideo"]["id"], high_resolution=False, language='en'),
                                            YouTubeSubtitleFile(youtube_id=spec_mat["youtubeVideo"]["id"], language='en')
                                        ]
                                    )
                         
                                    assignment.add_child(video_node)
                                elif "link" in spec_mat:
                                    print("link")
                                    #Add this case with web scraping
                                
                                elif "form" in spec_mat:
                                    print("form")
                                    #Might not add this case
                                elif "driveFile" in spec_mat:

                                    docPath = "documents/" + slugify(spec_mat["driveFile"]["driveFile"]["title"]) + ".pdf"

                                    document_node = DocumentNode(
                                        source_id=spec_mat["driveFile"]["driveFile"]["id"],
                                        title=spec_mat["driveFile"]["driveFile"]["title"],
                                        language=getlang('en').id,
                                        license=get_license(licenses.CC_BY, copyright_holder='Copyright holder name'),
                                        thumbnail=None,
                                        files=[DocumentFile(
                                                    path=str(docPath),
                                                    language=getlang('en').id
                                            )]
                                    )
                                    assignment.add_child(document_node)
                                    
                                    
                                   
                              

                 
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

#!/usr/bin/env python
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import ChannelNode, TopicNode, DocumentNode
from ricecooker.classes.files import DocumentFile
from ricecooker.classes.licenses import get_license
import json



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
                    assignment = TopicNode(title = a_info['title'], source_id = a_info['id'], description = a_info['description'])

                    if a_info['topicId'] == t_info['topicId']:
                        topic.add_child(assignment)

                 
            return channel

        


if __name__ == "__main__":
    """
    Run this script on the command line using:
        python sushichef.py  --token=YOURTOKENHERE9139139f3a23232
    """
    simple_chef = MyChef()
    simple_chef.main()
# i4i-GoogleClassroomKolibri

HOW TO RUN

1. Run gc_scraper.py in command line
2. Provide access to the google account connected to the Google Classroom course you wish to access
3. Select the course number when prompted.
4. Run kolibri_uploader.py and provide your token when prompted.
5. The uploader should take the JSON file created by the scraper and create the kolibri channel.
6. At this point you must log on to Kolibri Studio, open the created channel, 
   and hit the update button to see your changes.



Find your individual Kolibri Studio token at https://studio.learningequality.org/settings/tokens

Must have python installed as well as the google classroom, google drive and ricecooker apis.

https://developers.google.com/classroom/quickstart/python
https://ricecooker.readthedocs.io/en/latest/installation.html
https://developers.google.com/drive/api/v3/quickstart/python

My google classroom api credential file is provided but you can get your own at the link above.
You must authorize google drive by adding it to your api project at this link https://console.developers.google.com/

Also pip install slugify

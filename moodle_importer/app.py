import os
from moodle import MoodleClient, MoodleIntegrationManager

client = MoodleClient('https://rudie.moodlecloud.com', '0461b4a7e65e63921172fa3727f0863c')

client.sync()

# manager = MoodleIntegrationManager()
#
# manager.update_jupyterhub()

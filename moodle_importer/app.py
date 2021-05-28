import os
from unittest import mock
from moodle import MoodleClient, IntegrationManager

# client = MoodleClient('https://rudie.moodlecloud.com', '0461b4a7e65e63921172fa3727f0863c')
#
# client.sync()

manager = IntegrationManager()


with mock.patch('moodle.integration.manager.open') as mocked_open:
    with mock.patch('moodle.integration.system.os.system', autospec=True) as mocked_os:
        manager.update_jupyterhub()
        print(mocked_os.call_args_list)
        print(mocked_open.call_args_list)

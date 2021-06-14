import os
from unittest import mock

from moodle import IntegrationManager, MoodleClient

client = MoodleClient('https://rudie2.moodlecloud.com',
                      'b49da0b28a719a0b2373bb41447c51d0')

print(MoodleClient.functions)

client.sync()

manager = IntegrationManager()

default_configuration = open(IntegrationManager.path.in_file).read()

with mock.patch(
            'moodle.integration.manager.open',
            new=mock.mock_open(read_data=default_configuration),
        ) as mocked_open:
    with mock.patch('moodle.integration.system.os.system', autospec=True) as mocked_os:
        manager.update_jupyterhub()
        print(mocked_os.call_args_list)
        print(mocked_open.call_args_list)
        print(mocked_open().write.call_args_list)

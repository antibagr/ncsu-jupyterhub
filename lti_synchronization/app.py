# import os
# from unittest import mock
# from pprint import pprint
#
# from dotenv import load_dotenv
#
# from moodle import MoodleClient
#
#
# load_dotenv(verbose=True)
#
# client = MoodleClient()
#
# client.use_categories()
#
# client.download_json()
#
# pprint(client.courses)


#
# manager = IntegrationManager()
#
# default_configuration = open(IntegrationManager.path.in_file).read()
#
# with mock.patch(
#             'moodle.integration.template.open',
#             new=mock.mock_open(read_data=default_configuration),
#         ) as mocked_open:
#     with mock.patch('moodle.integration.system.os.system', autospec=True) as mocked_os:
#
#         manager.update_jupyterhub()
#
#         print(mocked_os.call_args_list)
#
#         print(mocked_open.call_args_list)

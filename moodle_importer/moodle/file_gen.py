"""
File generator
"""
import os
import re
import typing as t

from .processor import Processor

from .typehints import JsonType


class FileGenerator(Processor):

    def __init__(self) -> None:

        self._temp_fn = self.BASE_DIR / 'data' / 'template.py'
        self._out_fn = self.BASE_DIR / 'data' / 'jupyterhub_config.py'

        super().__init__()


    def generate(self):
        '''
        Read 'data.json' and generate jupyterhub_config.py
        Replacing placeholders in template.py
        '''

        with open(self._temp_fn, 'r') as f:
            template = f.read()

        if os.path.exists(self._out_fn):
            print(f'Warning! Old {self._out_fn} will be overwritten.')

        with open(self._out_fn, 'w') as f:

            f.write(template.format(**self._parse_data()))


    def _parse_data(self) -> JsonType:

        courses = self.load_json()

        admin_users = set()

        whitelist = set()

        groups = {}

        services = []

        for course in courses:

            course_id: str = re.sub('\W', '_', course['short_name'].lower())

            service = {
                'name': course_id,
                'url': 'http://127.0.0.1:9999',
                'command': [
                    'jupyterhub-singleuser',
                    f'--group=formgrade-{course_id}',
                    '--debug',
                ],
                'user': f'grader-{course_id}',
                'cwd': f'/home/grader-{course_id}',
                'api_token': ''  # include api token from admin user
            }

            services.append(service)

            admin_users.update(x['username'] for x in course['instructors'])

            group_name = f'formgrade-{course_id}'

            for grader in course['instructors'] + course['graders']:

                if group_name in groups:
                    groups[group_name].append(grader['username'])
                else:
                    groups[group_name] = [grader['username']]

            groups[f'nbgrader-{course_id}'] = []

            users = course['instructors'] + course['graders'] + course['students']

            whitelist.update(user['username'] for user in users)

        return {
            'admin_users': admin_users,
            'whitelist': whitelist,
            'groups': groups,
            'services': services,
        }

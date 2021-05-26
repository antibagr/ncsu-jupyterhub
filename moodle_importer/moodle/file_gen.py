"""
File generator
"""

import json
import logging
import os
import re
import shutil
import subprocess
import typing as t
from pathlib import Path
from secrets import token_hex

from moodle.settings import BASE_DIR, EXCHANGE_DIR, NB_GID, NB_UID
from moodle.templates import (JUPYTERHUB_USERS,
                              NBGRADER_COURSE_CONFIG_TEMPLATE,
                              NBGRADER_HOME_CONFIG_TEMPLATE,
                              NBGRADER_HOME_CONFIG_TEMPLATE_SHORT)
from nbgrader.api import Assignment, Course, Gradebook, InvalidEntry

from .processor import Processor
from .typehints import JsonType

# from sqlalchemy_utils import create_database
# from sqlalchemy_utils import database_exists


class FileGenerator(Processor):

    def __init__(self) -> None:

        self._temp_fn = self.BASE_DIR / 'jupyterhub_config.py'

        self._out_fn = '/srv/jupyterhub/jupyterhub_config.py'

        self._tokens_fn = self.BASE_DIR / 'data' / 'tokens.json'

        self.admin_users: t.Set = set()
        self.whitelist: t.Set = set()

        self.courses: JsonType = []

        self.groups: JsonType = {}
        self.tokens: t.Dict[str, str] = {}

        self.services: t.List[dict] = []

        super().__init__()

    def generate(self):
        '''
        Read 'data.json' and generate jupyterhub_config.py
        Replacing placeholders in template.py
        '''

        with open(self._temp_fn, 'r') as f:
            base_config = f.read()

        assert base_config

        if os.path.exists(self._out_fn):
            print(f'Warning! Old {self._out_fn} will be overwritten.')

        self.parse_data()

        assert self.groups and self.admin_users

        with open(self._out_fn, 'w') as f:

            f.write(base_config + JUPYTERHUB_USERS.format(**{
                'admin_users': self.admin_users,
                'whitelist': self.whitelist,
                'groups': self.groups,
                'tokens': self.tokens,
                'services': self.services,
            }))

        with open(self._tokens_fn, 'w') as f:
            json.dumps(self.tokens)

    def add_users(self):

        courses = self.load_json()

        with open(self._tokens_fn, 'r') as f:
            tokens = {v: k for k, v in json.loads(f)}

        for course in courses:

            course_id = course['short_name']

            os.environ['JUPYTERHUB_USER'] = f'grader-{course_id}'

            os.environ['JUPYTERHUB_API_TOKEN'] = tokens[f'grader-{course_id}']

            for user in course['instructors'] + course['graders'] + course['students']:

                os.system(f'''
nbgrader db student add {user["username"]} --last-name={user["last_name"]} --first-name={user["first_name"]} \
--course-dir=/home/grader-{course_id}/{course_id} \
--CourseDirectory.course_id={course_id} \
--email={user["email"]} \
--db=sqlite:////home/grader-{course_id}/{course_id}_grader.db
''')

    def create_service(self, course_id: str, api_token: str, port: int = 0) -> dict:
        return {
            'name': course_id,
            "admin": True,
            'url': f'http://127.0.0.1:{9000 + port}',
            'command': [
                'jupyterhub-singleuser',
                f'--group=formgrade-{course_id}',
                '--debug',
                '--allow-root',
            ],
            'user': f'grader-{course_id}',
            'cwd': f'/home/grader-{course_id}',
            'api_token': api_token,
            'environment': {'JUPYTERHUB_SERVICE_USER': f'grader-{course_id}'}
        }

    def update_services(self, grader: str, course_id: str, port: int = 0) -> None:

        service_token = token_hex(32)

        self.tokens[service_token] = grader

        self.services.append(
            self.create_service(
                course_id, service_token, port
            )
        )

    def update_admins(self, course: dict, grader: str) -> None:

        self.admin_users.update(x['username'] for x in course['instructors'])
        self.admin_users.add(grader)

    def write_config(self, path: str, course_id: str, home: bool = False) -> None:

        if home:
            path = '/home/' + path

        print(f'writing config file for [{course_id}] {path}')

        with open(f'{path}/nbgrader_config.py', 'w') as f:
            f.write(
                NBGRADER_HOME_CONFIG_TEMPLATE_SHORT.format(
                    db_url='sqlite:///'
                    + f'/home/grader-{course_id}/grader.db',
                )
            )

    def write_grader_config(self, grader: str, course_id: str) -> None:

        print(f'Writing grader config for [{course_id}] {grader}')

        with open(f'/home/{grader}/.jupyter/nbgrader_config.py', 'w') as f:
            f.write(
                NBGRADER_HOME_CONFIG_TEMPLATE.format(
                    grader_name=grader,
                    course_id=course_id,
                    db_url='sqlite:///' + f'/home/{grader}/grader.db'
                )
            )

        with open(f'/home/{grader}/{course_id}/nbgrader_config.py', 'w') as f:
            f.write(
                NBGRADER_COURSE_CONFIG_TEMPLATE.format(course_id=course_id)
            )

    def create_user(self, username: str) -> None:

        print(f'>>> Creating user {username}')

        os.system(f'adduser -q --gecos "" --disabled-password {username}')
        # os.system(f'chmod 664 /home/{username}')
        # os.system(f'chown -R {username}:{username} /home/{username}')
        ...

    def create_grader(self, grader: str, course_id: str) -> None:

        self.create_user(grader)

        course_dir = Path(f'/home/{grader}/{course_id}')

        jupyter = str(course_dir.parent / '.jupyter')

        os.system(f'mkdir -p {jupyter} {course_dir / "source"}')
        os.system(f'chown -R {grader}:{grader} {jupyter} {course_dir / "source"}')

        self.write_grader_config(grader, course_id)

    def get_db(self, grader: str, course_id: str) -> Gradebook:
        return Gradebook(f'sqlite:////home/{grader}/grader.db', course_id=course_id)

    def parse_data(self) -> None:

        self.courses = self.load_json()

        for course in self.courses:

            course_id: str = re.sub('\W', '_', course['short_name'].lower())

            grader = f'grader-{course_id}'

            group_name = f'formgrade-{course_id}'

            self.update_services(grader, course_id, self.courses.index(course))

            self.update_admins(course, grader)

            self.groups[group_name] = []

            self.create_grader(grader, course_id)

            self.groups[group_name].append(grader)

            self.whitelist.add(grader)

            course_db = self.get_db(grader, course_id)

            for user in course['instructors'] + course['graders'] + course['students']:

                username: str = user['username']

                if user['role'] != 'student':

                    self.groups[group_name].append(user['username'])

                if user['role'] not in ('teacher', 'editingteacher', 'instructor'):

                    course_db.update_or_create_student(
                        user['username'],
                        first_name=user['first_name'],
                        last_name=user['last_name'],
                        email=user['email'],
                        lms_user_id=user['id'],
                    )

                self.create_user(username)

                self.whitelist.add(username)

                self.write_config(username, course_id, home=True)

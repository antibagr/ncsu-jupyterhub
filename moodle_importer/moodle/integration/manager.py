import os
import typing as t
from secrets import token_hex
from pathlib import Path

from loguru import logger

from moodle.file_worker import FileWorker
from moodle.integration.helper import IntegrationHelper
from moodle.integration.template import Templater
from moodle.integration.system import SystemCommand
from moodle.typehints import Course, JsonType, User
from moodle.templates import JUPYTERHUB_USERS
from moodle.settings import BASE_DIR
from moodle.utils import grader


class IntegrationManager:

    helper: IntegrationHelper
    temp: Templater

    admin_users: t.Set
    whitelist: t.Set

    courses: JsonType

    groups: JsonType
    tokens: t.Dict[str, str]

    services: t.List[dict]

    def __init__(self):

        self.helper = IntegrationHelper()

        self.temp = Templater()

        self.system = SystemCommand()

        self.admin_users: t.Set = set()

        self.whitelist: t.Set = set()

        self.courses: JsonType = []

        self.groups: JsonType = {}

        self.tokens: t.Dict[str, str] = {}

        self.services: t.List[dict] = []

    def update_services(self, course_id: str, port: int = 0) -> None:

        service_token = token_hex(32)

        self.tokens[service_token] = grader / course_id

        self.services.append(
            self.temp.create_service(course_id, service_token, port)
        )

    def update_admins(self, course: Course) -> None:

        self.admin_users.update(x['username'] for x in course['instructors'])
        self.admin_users.add(grader / course['short_name'])

    def create_grader(self, course_id: str) -> None:

        course_grader: str = grader / course_id

        self.system.create_user(course_grader)

        course_dir = Path(f'/home/{course_grader}/{course_id}')

        jupyter = f'/home/{course_grader}/.jupyter'

        self.system.create_dirs(jupyter, course_dir / 'source')

        self.temp.write_grader_config(course_id)

        self.system.chown(course_grader, jupyter, course_dir / 'source', course_dir, group=course_grader)

        self.system.enable_nbgrader(course_grader)

    def add_users(self, course: Course) -> None:

        for user in course['instructors'] + course['graders'] + course['students']:

            username: str = user['username']

            group: str = self.helper.get_user_group(user)

            self.whitelist.add(username)

            if group != 'students':

                self.groups[f'formgrade-{course["short_name"]}'].append(username)

            else:

                self.groups[f'nbgrader-{course["short_name"]}'].append(username)

                self.helper.add_student(course["short_name"], user)

            self.system.create_user(username)



    def load_course(self, course: Course):

        course_id: str = self.helper.format_string(course['short_name'])

        self.update_services(course_id, self.courses.index(course))

        self.update_admins(course)

        self.groups.update({
                f'formgrade-{course_id}': [grader / course_id, ],
                f'nbgrader-{course_id}': [],
        })

        self.create_grader(course_id)

        self.whitelist.add(grader / course_id)

        self.add_users(course)

    def load_data(self) -> None:

        self.courses = FileWorker().load_json()

        logger.debug(f'{len(self.courses)} courses found: {", ".join([x["title"] for x in self.courses])}')

        for course in self.courses:

            self.load_course(course)

    def update_jupyterhub(self):
        '''
        Read 'data.json' and generate jupyterhub_config.py
        Replacing placeholders in template.py
        '''

        in_file: Path = BASE_DIR / 'jupyterhub_config.py'
        out_file: str = '/srv/jupyterhub/jupyterhub_config.py'

        with open(in_file, 'r') as f:
            default_configuration = f.read()

        if not default_configuration:

            logger.error(f'Template file {in_file} file is empty.')

        if os.path.exists(out_file):

            logger.warning(f'Old {out_file} will be overwritten.')

        self.load_data()

        with open(out_file, 'w') as jupyterhub_config:

            jupyterhub_config.write(
                default_configuration +
                JUPYTERHUB_USERS.format(**{
                    'admin_users': self.admin_users,
                    'whitelist': self.whitelist,
                    'groups': self.groups,
                    'tokens': self.tokens,
                    'services': self.services,
                }
            ))

        logger.info(f'Successfully update {out_file}')

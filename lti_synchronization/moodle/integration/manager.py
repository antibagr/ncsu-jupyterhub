import typing as t
from collections import defaultdict
from contextlib import suppress
from operator import itemgetter
from pathlib import Path
from secrets import token_hex

from loguru import logger
from moodle.file_worker import FileWorker
from moodle.helper import NBGraderHelper
from . import system
from .template import Templater
from moodle.settings import BASE_DIR
from moodle.typehints import Course, JsonType, User, PathLike
from moodle.utils import grader, JsonDict


class SyncManager:
    '''
    Manager class for setup Jupyterhub with data received from Moodle.

    Attributes:
        admin_users (set): Set of users with admin permissions. Such as instructors.
        whitelist (set): All users enrolled in all the courses.
        courses (JsonType): Formatted courses with enrolled students.
        groups (JsonType): One of nbgrader-{course_id} or formgrader-{course_id}
                           Group name defined whether a user is a student or a grader.
        tokens (type): Unique keys that allow services to access Jupyterhub.
        services (type): A service (local notebook server) for every course
                         will be created in order to be accessible for graders
                         and instructors.

    '''

    class path:

        # default configuration template
        in_file: Path = BASE_DIR / 'default_jupyterhub_config.py'

        # production jupyterhub configuration
        out_file: Path = Path('/srv/jupyterhub/jupyterhub_config.py')

    helper: NBGraderHelper

    temp: Templater

    admin_users: set

    whitelist: set

    courses: t.List[Course]

    groups: defaultdict

    tokens: t.Dict[str, str]

    services: t.List[dict]

    def __init__(self):

        self.helper = NBGraderHelper()

        self.temp = Templater()

        self.admin_users = set()
        self.whitelist = set()

        self.courses = []
        self.groups = defaultdict(list)

        self.tokens = {}
        self.services = []

    def update_services(self, course_id: str, port: int = 0) -> None:
        '''
        Generate new service token. Add new token to self.tokens
        And generate new service with such token.

        Args:
            course_id (str): Normalized course name.
            port (int): A Port that service should take. Defaults to 0.
        '''

        service_token = token_hex(32)

        self.tokens[service_token] = grader / course_id

        self.services.append(
            self.temp.create_service(course_id, service_token, port)
        )

    def update_admins(self, course: Course) -> None:
        '''
        Update admin_users set with instructors from the course.
        Add a grader to admin users.

        Args:
            course (Course): Target course.
        '''

        self.admin_users.update(x['username'] for x in course['instructors'])
        self.admin_users.add(grader / course['short_name'])

    def create_grader(self, course_id: str) -> None:
        '''
        Create new UNIX user with appropriate directories.
        Write nbgrader_config files in home and course's root dirs.
        Change owner of these files to a grader and set Readonly permissions.
        Enable all nbgrader extensions for the grader.

        Args:
            course_id (str): Normalized course name.
        '''

        course_grader: str = grader / course_id

        system.create_user(course_grader)

        course_dir = Path(f'/home/{course_grader}/{course_id}')

        jupyter = f'/home/{course_grader}/.jupyter'

        system.create_dirs(jupyter, course_dir / 'source')

        self.temp.write_grader_config(course_id)

        system.chown(course_grader, jupyter, course_dir / 'source', course_dir, group=course_grader)

        system.enable_nbgrader(course_grader)

    def add_users(self, course: Course) -> None:
        '''
        Iterate by instructors, graders, and students.
        Add every user to the appropriate group.
        Add students to nbgrader database, and add
        UNIX users for every enrolled participant.

        Args:
            course (Course): Course contains the users.

        '''

        graders_group = f'formgrade-{course["short_name"]}'
        students_group = f'nbgrader-{course["short_name"]}'

        for user in course['instructors'] + course['graders'] + course['students']:

            username: str = user['username']

            group: str = self.helper.get_user_group(user)

            self.whitelist.add(username)

            if group != 'students':

                self.groups[graders_group].append(username)

            else:

                self.groups[students_group].append(username)

                self.helper.add_student(course['short_name'], user)

            system.create_user(username)

    def load_course(self, course: Course) -> None:
        '''
        Create course's service, add course instructors as admin users.
        Create course's groups and add users to them.

        Args:
            course (Course): Target course
        '''

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
        '''
        Read data fetched from Moodle and load courses into self.
        '''

        _titles = []

        for raw_course in FileWorker().load_json():

            course = JsonDict(raw_course)

            self.courses.append(course)

            _titles.append(course.title)

        logger.debug(f'{len(_titles)} courses found: {", ".join(_titles)}')

        for course in self.courses:

            self.load_course(course)

    def update_jupyterhub(
            self,
            in_file: t.Optional[PathLike] = None,
            out_file: t.Optional[PathLike] = None,
        ) -> None:
        '''Updates jupyterhub_config file with data received from Moodle LMS.

        After calling moodle.client.api.MoodleClient.download_json method,
        formatted json file should be available on the disk system.
        We can now synchronize Jupyterhub configuration file using the data
        about courses and enrolled users.

        Args:
            in_file (t.Optional[PathLike]):
                Pass template file if it differs from default. Defaults to None
            out_file (t.Optional[PathLike]):
                Pass jupyterhub_config location if it differs from default.
                Defaults to None.
        '''

        with suppress(KeyboardInterrupt):

            default_config: str = self.temp.get_default_jupyterhub_config(
                in_file or self.path.in_file)

            self.load_data()

            self.temp.update_jupyterhub_config(
                out_file or self.path.out_file,
                default_config,
                **{
                    'admin_users': self.admin_users,
                    'whitelist': self.whitelist,
                    'groups': dict(self.groups),
                    'tokens': self.tokens,
                    'services': self.services,
                }
            )

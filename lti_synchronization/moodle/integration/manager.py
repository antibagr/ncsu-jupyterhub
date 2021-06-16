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
        '''Add new Jupyterhub service to data.

        We don't interact with OS or API there, rather create a dictionary
        filled with course specific data which will be passed into c.Services
        in the jupyterhub_config file. To communicate with services, Jupyterhub
        uses tokens which are randomly generated strings. To allow services
        talk back to Jupyterhub, we need to map these tokens to services' names
        in the configuration file as well.

        Notice that port argument is the offset from 9000. So if you pass
        1, the port would be 9001

        Args:
            course_id (str): Normalized course name.
            port (int): A Port offset that service should take. Defaults to 0.
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

        self.admin_users.update(user.username for user in course.instructors)
        self.admin_users.add(grader / course.course_id)

    def create_grader(self, course_id: str) -> None:
        '''Create daemon user for hosting a course server.

        Here we have some low-level OS operations. A lot of errors occur
        because nbgrader heavily relate on file hierarchy and file permissions.

        To launch new service properly, a user should exist on the system.
        Then you need to create several directories and write nbgrader_config
        which will point to the course source files location. With this done,
        we need to set appropriate permissions to database file and course
        directories and enable nbgrader extensions, since only instructors and
        graders can login to the service.

        Args:
            course_id (str): Normalized course name.
        '''

        course_grader: str = grader / course_id

        system.create_user(course_grader)

        course_dir = Path(f'/home/{course_grader}/{course_id}')

        jupyter = f'/home/{course_grader}/.jupyter'

        system.create_dirs(jupyter, course_dir / 'source')

        self.temp.write_grader_config(course_id)

        system.chown(course_grader, jupyter, course_dir
                     / 'source', course_dir, group=course_grader)

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

        graders_group = f'formgrade-{course.course_id}'
        students_group = f'nbgrader-{course.course_id}'

        for user in course.instructors + course.graders + course.students:

            username: str = user.username

            group: str = self.helper.get_user_group(user)

            self.whitelist.add(username)

            if group != 'students':

                self.groups[graders_group].append(username)

            else:

                self.groups[students_group].append(username)

                self.helper.add_student(course.course_id, user)

            system.create_user(username)

    def process_course(self, course: Course) -> None:
        '''Process data neccesary to configure Jupyterhub, interacts with OS.

        Let's assume we have one new course in JSON called 'foo'

        To set up new course in the nbgrader, couple of conditions should be
        satisfied.

            New service should be created:
                In order to allow multiple users to work on the same files
                simultaniously, we need to create new Jupyterhub service,
                generate API token and create daemon user to host it. After
                re-deploying, grades will be able to access this service via
                services menu in Jupyterhub.

            Read more about Jupyterhub services:
                https://jupyterhub.readthedocs.io/en/stable/reference/services.html

            Two Jupyterhub groups should be created:
                'formgrade-foo' for instructors, graders, and teachers
                'nbgrader-foo' for students to access the course.

            Deamon user called 'foo-grader' to host the service

            Add all enrolled users to whitelist, since all login attemts from
            users that's not in the whitelist will be blocked

            Add instructors to admin user list

            Create UNIX users to all enrolled participant

            Read more about Jupyterhub user management:
                https://jupyterhub.readthedocs.io/en/stable/getting-started/authenticators-users-basics.html


        Since there is no way to generate new service programmaticaly,
        we need to update jupyterhub_config file and restart hub for the
        changes to apply. That's because synchronize must be initiate from
        outside of the Jupyterhub container.

        Args:
            course (Course): Course to process.
        '''

        self.update_services(course.course_id, self.courses.index(course))

        self.update_admins(course)

        self.groups.update({
                f'formgrade-{course.course_id}': [grader / course.course_id, ],
                f'nbgrader-{course.course_id}': [],
        })

        self.create_grader(course.course_id)

        self.whitelist.add(grader / course.course_id)

        self.add_users(course)

    def process_data(self, json_path: t.Optional[PathLike] = None) -> None:
        '''Iterates through JSON file and calls self.process_course for
        every course found in a file.

        Args:
            json_path (t.Optional[PathLike]):
                Custom path to JSON. Defaults to None.
        '''

        courses = (JsonDict(crs) for crs in FileWorker(json_path).load_json())

        for course in courses:

            logger.debug(f'Processing coure {course.title!r}')

            self.courses.append(course)

            self.process_course(course)

    def update_jupyterhub(
                self,
                *,
                json_path: t.Optional[PathLike] = None,
                in_file: t.Optional[PathLike] = None,
                out_file: t.Optional[PathLike] = None,
            ) -> None:
        '''Updates jupyterhub_config file with data received from Moodle LMS.

        After calling moodle.client.api.MoodleClient.download_json method,
        formatted json file should be available on the disk system.
        We can now synchronize Jupyterhub configuration file using the data
        about courses and enrolled users.

        Args:
            json_path (t.Optional[PathLike]):
                JSON source file path if it differs from default. Defaults to None
            in_file (t.Optional[PathLike]):
                template file if it differs from default. Defaults to None
            out_file (t.Optional[PathLike]):
                jupyterhub_config location if it differs from default. Defaults to None.
        '''

        with suppress(KeyboardInterrupt):

            default_config: str = self.temp.get_default(in_file or self.path.in_file)

            self.process_data(json_path)

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

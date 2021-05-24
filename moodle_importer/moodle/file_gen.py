"""
File generator
"""
import os
import logging
import re
import typing as t
from pathlib import Path
import shutil

from secrets import token_hex

from nbgrader.api import Assignment
from nbgrader.api import Course
from nbgrader.api import Gradebook
from nbgrader.api import InvalidEntry
# from sqlalchemy_utils import create_database
# from sqlalchemy_utils import database_exists

from .processor import Processor

from .typehints import JsonType

from moodle.templates import (NBGRADER_COURSE_CONFIG_TEMPLATE, NBGRADER_HOME_CONFIG_TEMPLATE, JUPYTERHUB_USERS)
from moodle.settings import BASE_DIR, EXCHANGE_DIR, NB_UID, NB_GID

class FileGenerator(Processor):

    def __init__(self) -> None:

        self._temp_fn = self.BASE_DIR / 'data' / 'template.py'
        self._out_fn = '/srv/jupyterhub/jupyterhub_config.py'

        super().__init__()

    def generate(self):
        '''
        Read 'data.json' and generate jupyterhub_config.py
        Replacing placeholders in template.py
        '''

        with open(self._temp_fn, 'r') as f:
            base_config = f.read()

        if os.path.exists(self._out_fn):
            print(f'Warning! Old {self._out_fn} will be overwritten.')

        with open(self._out_fn, 'w') as f:

            f.write(base_config + JUPYTERHUB_USERS.format(**self._parse_data()))

    def _parse_data(self) -> JsonType:

        courses = self.load_json()

        admin_users = set()

        whitelist = set()

        groups = {}

        services = []

        for course in courses:

            course_id: str = re.sub('\W', '_', course['short_name'].lower())

            nb_helper = NbGraderServiceHelper(course_id)

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
                'api_token': token_hex(32),
            }

            services.append(service)

            admin_users.update(x['username'] for x in course['instructors'])

            group_name = f'formgrade-{course_id}'

            users = course['instructors'] + course['graders'] + course['students']

            groups[group_name] = []

            for user in users:

                if user['role'] != 'student':

                    groups[group_name].append(user['username'])

                user_home: Path = Path(f'/home{user["username"]}')

                user_home.mkdir(parents=True, exist_ok=True)

                # user_home.joinpath('nbgrader_config.py').write_text(
                # NBGRADER_COURSE_CONFIG_TEMPLATE.format(
                #     course_id=course_id
                # )
                # )

                nb_helper.add_user_to_nbgrader_gradebook(user['username'], user['id'])
                whitelist.add(user['username'])

            groups[group_name].append(f'grader-{course_id}')
            whitelist.add(f'grader-{course_id}')

            self._create_grader_directories(course_id)

            self._create_nbgrader_files(course_id)

        return {
            'admin_users': admin_users,
            'whitelist': whitelist,
            'groups': groups,
            'services': services,
        }

    def _create_grader_directories(self, course_id: str) -> None:
        """
        Creates home directories with specific permissions
        Directories to create:
        - grader_root: /home/grader-<course-id>
        - course_root: /home/grader-<course-id>/<course-id>
        """

        course_dir = Path(f'/home/grader-{course_id}/{course_id}')

        course_dir.mkdir(parents=True, exist_ok=True)

        # change the course directory owner
        shutil.chown(str(course_dir), user=NB_UID, group=NB_GID)
        shutil.chown(str(course_dir.parent), user=NB_UID, group=NB_GID)

    def _create_nbgrader_files(self, course_id: str) -> None:
        """
        Creates nbgrader configuration files
        used in the grader's home directory
        and the course directory located
        within the grader's home directory.
        """

        course_dir = Path(f'/home/grader-{course_id}/{course_id}')

        # create the .jupyter directory (a child of grader_root)
        jupyter_dir = course_dir.parent.joinpath(".jupyter")
        jupyter_dir.mkdir(parents=True, exist_ok=True)

        shutil.chown(str(jupyter_dir), user=NB_UID, group=NB_GID)

        grader_nbconfig_path = jupyter_dir.joinpath("nbgrader_config.py")

        grader_nbconfig_path.write_text(NBGRADER_HOME_CONFIG_TEMPLATE.format(
            grader_name=f'grader-{course_id}',
            course_id=course_id,
            db_url='sqlite:///srv/jupyterhub/grader.db'
        ))

        # Write the nbgrader_config.py file at grader home directory
        course_nbconfig_path = course_dir.joinpath("nbgrader_config.py")

        course_home_nbconfig_content = NBGRADER_COURSE_CONFIG_TEMPLATE.format(
            course_id=course_id
        )

        course_nbconfig_path.write_text(NBGRADER_COURSE_CONFIG_TEMPLATE.format(
            course_id=course_id
        ))

class NbGraderServiceHelper:
    """
    Helper class to use the nbgrader database and gradebook

    Attrs:
      course_id: the course id (equivalent to the course name)
      course_dir: the course directory located in the grader home directory
      uid: the user id that owns the grader home directory
      gid: the group id that owns the grader home directory
      db_url: the database string connection uri
      database_name: the database name
    """

    def __init__(self, course_id: str, check_database_exists: bool = False):
        if not course_id:
            raise ValueError("course_id missing")

        self.course_id = course_id
        self.course_dir = f"/home/grader-{self.course_id}/{self.course_id}"
        self.uid = int(os.environ.get("NB_GRADER_UID") or "10001")
        self.gid = int(os.environ.get("NB_GID") or "100")

        self.db_url = 'sqlite:////srv/jupyterhub/grader.db' # nbgrader_format_db_url(course_id)
        self.database_name = course_id
        if check_database_exists:
            self.create_database_if_not_exists()

    def create_database_if_not_exists(self) -> None:
        """Creates a new database if it doesn't exist"""

        raise Exception()
        # conn_uri = nbgrader_format_db_url(self.course_id)
        #
        # if not database_exists(conn_uri):
        #     logger.debug("db not exist, create database")
        #     create_database(conn_uri)

    def add_user_to_nbgrader_gradebook(self, username: str, lms_user_id: str) -> None:
        """
        Adds a user to the nbgrader gradebook database for the course.

        Args:
            username: The user's username
            lms_user_id: The user's id on the LMS
        Raises:
            InvalidEntry: when there was an error adding the user to the database
        """
        if not username:
            raise ValueError("username missing")
        if not lms_user_id:
            raise ValueError("lms_user_id missing")

        with Gradebook(self.db_url, course_id=self.course_id) as gb:
            try:
                gb.update_or_create_student(username, lms_user_id=lms_user_id)
                logging.debug(
                    "Added user %s with lms_user_id %s to gradebook"
                    % (username, lms_user_id)
                )
            except InvalidEntry as e:
                logger.debug("Error during adding student to gradebook: %s" % e)

    def update_course(self, **kwargs) -> None:
        """
        Updates the course in nbgrader database
        """
        with Gradebook(self.db_url, course_id=self.course_id) as gb:
            gb.update_course(self.course_id, **kwargs)

    def get_course(self) -> Course:
        """
        Gets the course model instance
        """
        with Gradebook(self.db_url, course_id=self.course_id) as gb:
            course = gb.check_course(self.course_id)
            logger.debug(f"course got from db:{course}")
            return course

    def register_assignment(self, assignment_name: str, **kwargs: dict) -> Assignment:
        """
        Adds an assignment to nbgrader database

        Args:
            assignment_name: The assingment's name
        Raises:
            InvalidEntry: when there was an error adding the assignment to the database
        """
        if not assignment_name:
            raise ValueError("assignment_name missing")
        logger.debug(
            "Assignment name normalized %s to save in gradebook" % assignment_name
        )
        assignment = None
        with Gradebook(self.db_url, course_id=self.course_id) as gb:
            try:
                assignment = gb.update_or_create_assignment(assignment_name, **kwargs)
                logger.debug("Added assignment %s to gradebook" % assignment_name)
            except InvalidEntry as e:
                logger.debug("Error ocurred by adding assignment to gradebook: %s" % e)
        return assignment

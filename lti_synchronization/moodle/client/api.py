import typing as t
from functools import wraps
from contextlib import suppress

from loguru import logger
from moodle.client.base import BaseAPIClient
from moodle.client.helper import MoodleDataHelper
from moodle.file_worker import FileWorker
from moodle.response import FluidResponse
from moodle.settings import ROLES
from moodle.typehints import Course, JsonType, PathLike, User
from moodle.utils import log_load_data


class MoodleClient(BaseAPIClient):
    '''
    Client for fetch the data from the Moodle LMS.

    Args:
        url (str): Moodle server URL
        key (str): Secret API key
        endpoint (t.Optional[str]): Custom endpoint. Defaults to None.

    Attributes:
        functions: Tuple of functions need to be enabled in
            Site administration / Plugins / Web services / External services
    '''

    functions: t.Tuple[str, ...] = (
        'core_course_get_courses',
        'core_enrol_get_enrolled_users',
    )

    helper: MoodleDataHelper

    courses: t.List[Course]

    users: t.Dict[str, User]

    def __init__(self, url: str, key: str, endpoint: t.Optional[str] = None) -> None:

        self.helper = MoodleDataHelper()
        self.courses = []
        self.users = {}

        super().__init__(url, key, endpoint)

    def get_courses(self) -> FluidResponse:
        return self.call('core_course_get_courses')

    def get_users(self, course_id: int) -> FluidResponse:
        return self.call('core_enrol_get_enrolled_users', courseid=course_id)

    @log_load_data('courses')
    def load_courses(self):
        '''
        Store formatted courses from Moodle API to self.courses
        '''

        for course in self.get_courses():

            self.courses.append(self.helper.format_course(course))

    @log_load_data('users')
    def load_users(self) -> None:
        '''
        Load users from every course and transform data to convinience format.
        Store users to course's group and self.users.
        '''

        for course in self.courses:

            # Call Moodle API
            course_users = self.get_users(course['id'])

            logger.debug(
                f'course "{course["title"]}" has {len(course_users)} enrolled participants.')

            for course_user in course_users:

                user: User = self.helper.format_user(course_user)

                user_roles = user.pop('roles', None)

                if user['username'] not in self.users:
                    self.users[user['username']] = user

                if user_roles:

                    # Find the most crucial role in a list
                    user['role']: str = self.helper.get_user_highest_role(
                        user_roles)

                    group: str = self.helper.get_user_group(user)

                    course[group].append(user)

    def sync(self, filename: t.Optional[PathLike] = None) -> None:
        '''
        Top-level method to load courses,
        load users from every course,
        transform them, and then
        store them to json file.
        '''

        with suppress(KeyboardInterrupt):

            self.load_courses()

            self.load_users()

            FileWorker(filename).save_json(self.courses)

            logger.info('Successfully update json')

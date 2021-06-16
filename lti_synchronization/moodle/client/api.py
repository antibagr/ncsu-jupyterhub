import os
from pprint import pprint
import typing as t
from contextlib import suppress

from loguru import logger
from moodle.client.base import BaseAPIClient
from moodle.client.helper import MoodleDataHelper
from moodle.file_worker import FileWorker
from moodle.response import FluidResponse
from moodle.settings import ROLES
from moodle.typehints import Course, PathLike, User
from moodle.utils import log_load_data, JsonDict


class MoodleClient(BaseAPIClient):
    '''Client for fetch the data from the Moodle LMS.

    Mainly used to generate JSON file from Moodle courses and users REST
    responses, but also can be used to low-level API calls
    (see moodle.client.base.BaseAPIClient for low-level details)

    It's important to note that reading documentation before using the client
    in the production enviroment is highly encouraged, because of its flexible
    mechanism to determine which course should use Jupyterhub and / or nbgrader.

    Attributes:
        functions:
            Tuple of functions need to be enabled in
            Site administration / Plugins / Web services / External services
    '''

    functions: t.Tuple[str, ...] = (
        'core_course_get_courses',
        'core_enrol_get_enrolled_users',
    )

    helper: MoodleDataHelper

    courses: t.List[Course]

    users: t.Dict[str, User]

    def __init__(self, *args: t.Any, **kwargs: t.Any):

        super().__init__(*args, **kwargs)

        self.helper = MoodleDataHelper()
        self.courses = []
        self.users = {}
        self._cats = ()
        self._use_categories = False

    def _get_users(self, course: Course) -> t.Generator[User, None, None]:
        '''Fetches users from a course and creates generator with them.

        Args:
            course (Course):
                Object with 'title' and 'id' attributes.

        Returns:
            t.Generator[User, None, None]:
                Generator with formatted users.

        '''

        resp: FluidResponse = self.call('core_enrol_get_enrolled_users',
                                        courseid=course.id)

        logger.debug(
            f'course {course.title!r} has {len(resp)} enrolled participants.')

        for raw_user in resp:

            yield self.helper.format_user(raw_user)

    def _get_courses(self) -> t.Generator[Course, None, None]:
        '''Fetches all courses from Moodle and creates generator with them.

        Returns:
            t.Generator[Course, None, None]: Generator with formatted courses.

        '''

        resp: FluidResponse = self.call('core_course_get_courses')

        for raw_course in resp:

            yield self.helper.format_course(raw_course)

    def get_categories(self) -> t.List[t.Tuple[str, str, str]]:
        '''Gets course title, short name, and category id for every course.

        It intends to make it easier to determine which id is assigned to
        'use jupyterhub' and 'use jupyterhub and nbgrader' categories. Since
        there is no way to set the category id manually. After you got the
        necessary id, put it to the environment variable (see use_categories
        property documentation for information on how to set up working with
        categories)

        Returns:
            t.List[t.Tuple[str, str, str]]:
                list where every course is represented as a tuple of title,
                short name, and category id.

        '''

        courses = []

        for course in self._get_courses():

            courses.append((course.title, course.course_id, course.category))

        return courses

    def use_categories(self) -> None:
        '''Forces the client to filter courses by category.

        If you call use_categories before fetching courses, we determine which
        course the client would add to Jupyterhub depends on categories ids.

        You need to create two categories in Moodle for courses that use only
        Jupyterhub and which use both nbgrader and Jupyterhub.  Then set the
        appropriate category to courses and call 'get_categories' method to
        show you course name and its category id. It's the only way to track
        category id since we can't set it manually.

        Then set environment variables MOODLE_JUPYTERHUB_CATEGORY_ID and
        MOODLE_NBGRADER_CATEGORY_ID with values you've received from Moodle.

        Raises:
            EnvironmentError:
                If env variables is not set.
        '''

        if self._use_categories:
            return

        self._use_categories = True

        env_jupyterhub = os.getenv('MOODLE_JUPYTERHUB_CATEGORY_ID')
        env_nbgrader = os.getenv('MOODLE_NBGRADER_CATEGORY_ID')

        if not env_jupyterhub:
            raise EnvironmentError('MOODLE_JUPYTERHUB_CATEGORY_ID is not set.')
        if not env_nbgrader:
            raise EnvironmentError('MOODLE_NBGRADER_CATEGORY_ID is not set.')

        try:
            self._cats = (int(env_jupyterhub), int(env_nbgrader))
        except ValueError:
            raise ValueError('MOODLE_JUPYTERHUB_CATEGORY_ID and '
                             'MOODLE_NBGRADER_CATEGORY_ID should be integers, representing '
                             'id of Moodle categories. You can determine them by calling '
                             'get_categories method.')

    @log_load_data('courses')
    def load_courses(self, **filters) -> None:
        '''Store courses from Moodle to self.courses

        There is two ways to select only courses that needs Jupyterhub
        and/or nbgrader support.

        First one is to use category id as a filter. In this case, call
        client.use_categories() once before calling any other method. The client
        will check if the course's category id equals either
        MOODLE_JUPYTERHUB_CATEGORY_ID or MOODLE_NBGRADER_CATEGORY_ID and will
        skip the course otherwise.

        Second option is to filter by course id, title, short_name or any other
        field available (see moodle.client.helper.MoodleDataHelper.format_course)

        If this behavior is disired, pass filters as keywords arguments.

        Examples:

            Filter courses by title::

                client.load_courses(title='some title')

            Filter by multiple fields::

                client.load_courses(title='some title', id=5)

            Filter with multiple options allowed::

                client.load_courses(title=('foo', 'bar'), id=(1, 5, 10))

        Note:
            Note that you can mix filters keywords and categories to filter
            the courses that already were filtered by categories.

        Args:
            **filters (type): .

        Returns:
            None: .

        '''

        def _skip_course(course) -> bool:
            '''
            Determine should the course be skipped according to provided filters
            '''

            for field, value in filters.items():

                # if provided filter is a sequence
                # check that course's value is in that sequence
                if not isinstance(value, str) and hasattr(type(value), '__iter__'):

                    if not value:
                        raise ValueError(f'Empty sequence found: {field}')

                    if course[field] not in value:
                        return True

                else:

                    if course[field] != value:
                        return True

            return False

        if self._use_categories:
            logger.info('Using category id to filter courses.')

        for course in self._get_courses():

            if self._use_categories and course.category not in self._cats:
                continue

            if _skip_course(course):
                continue

            self.courses.append(course)

    @log_load_data('users')
    def load_users(self) -> None:
        '''Iterates through self.courses and fetches users from that courses.

        We've got a lot of information about users from Moodle, but we don't
        need so much in Jupyterhub. To make it compact and helpful, we
        fetch users iteratively and find the role with the highest rank for
        every user (see moodle.client.helper.MoodleDataHelper for details)

        After the method called, users stores into courses' groups respectively
        to users' roles.

        '''

        for course in self.courses:

            for user in self._get_users(course):

                user_roles = user.pop('roles', None)

                if user.username not in self.users:
                    self.users[user.username] = user

                if user_roles:

                    # Find the most crucial role in a list
                    user.role: str = self.helper.find_highest_role(user_roles)

                    group: str = self.helper.get_user_group(user)

                    course[group].append(user)

    def download_json(self, json_path: t.Optional[PathLike] = None) -> None:
        '''Download formatted course data from Moodle as JSON.

        Before you hit this method, make sure to read about filtering courses
        in moodle.client.api.MoodleClient.load_courses method documentation,
        category filtering in moodle.client.api.MoodleClient.use_categories
        documentation, and user role resolving method in
        moodle.client.helper.MoodleDataHelper class documentation.

        Args:
            json_path (t.Optional[PathLike]):
                Path to JSON to be used over the default. Defaults to None.
        '''

        with suppress(KeyboardInterrupt):

            self.load_courses()

            self.load_users()

            try:
                FileWorker(json_path).save_json(self.courses)

            except OSError as exc:

                logger.exception(f'Failed to store JSON. Reason: {exc}')

                raise exc

            logger.info('Successfully update json')

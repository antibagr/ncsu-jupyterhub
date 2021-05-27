import typing as t
from functools import wraps

from loguru import logger

from moodle.client.base import BaseAPIClient
from moodle.file_worker import FileWorker
from moodle.response import FluidResponse
from moodle.settings import ROLES
from moodle.typehints import Course, JsonType, PathLike, User
from moodle.utils import format_course, format_user


def load_data(attr_name: str) -> t.Callable:
    '''
    Assume a func will store downloaded data to attr_name attribute,
    and we're able to get it's length.
    '''

    def _load_data(func: t.Callable) -> t.Callable:

        @wraps(func)
        def wrapper(self, *args: t.Any, **kw: t.Any) -> t.Any:

            logger.info(f'Loading {attr_name} ...')

            result = func(self, *args, **kw)

            logger.info(f'Loaded {len(getattr(self, attr_name))} {attr_name}.')

            return result
        return wrapper
    return _load_data


class MoodleInterface(BaseAPIClient):
    '''Convinient API wrapper'''

    def get_courses(self) -> FluidResponse:

        return self.call('core_course_get_courses')

    def get_users(self, course_id: int) -> FluidResponse:

        return self.call('core_enrol_get_enrolled_users', courseid=course_id)


class MoodleClient(MoodleInterface):

    courses: t.List[Course] = []

    users: t.Dict[str, User] = {}

    def __init__(self, url: str, key: str, endpoint: t.Optional[str] = None) -> None:

        self._load_roles()
        super().__init__(url, key, endpoint)

    def _load_roles(self) -> None:
        '''
        Cache dictionaries with roles.
        '''

        if hasattr(self, '_roles'):
            raise AttributeError('Roles already created.')

        self._roles = {k: v for k, v in zip(ROLES, range(len(ROLES)))}
        self._roles_reversed = {v: k for k, v in self._roles.items()}

    def priority(
                self,
                role: t.Union[str, int],
                reversed: bool = False
            ) -> t.Union[int, str]:
        '''Get the numeric rate of a role in order to find the most
        crucial in a list of roles.

        i.e. if the user has roles (student, TA) in a course
        The final role will be TA due to it has a higher role priority.

        Args:
            role (str): Role name in moodle. Should be in the ROLES tuple.
            reversed (bool): Map role by role's rate instead.

        Returns:
            t.Union[int, str]: Role rate or role name in reversed mode.

        '''

        return self._roles[role] if not reversed else self._roles_reversed[role]

    def get_user_highest_role(self, user_roles: t.List[str]) -> str:
        '''
        Get role with highest rank in a list of roles in user['roles'].

        Return:
            (str) - Role name.
        '''

        highest_rate: int = max(map(self.priority, user_roles))

        # user's highest role name
        return self.priority(highest_rate, reversed=True)

    def get_user_group(self, user: User) -> str:

        if user['role'] == 'student':
            group = 'students'
        elif user['role'] in ('editingteacher', 'manager', 'coursecreator', 'instructional_support'):
            group = 'instructors'
        elif user['role'] in ('teaching_assistant', 'teacher'):
            group = 'graders'
        else:
            raise KeyError(user['role'])

        return group

    @load_data('courses')
    def load_courses(self):
        '''
        Store formatted courses from Moodle API to self.courses
        '''

        for course in self.get_courses():

            self.courses.append(format_course(course))

    @load_data('users')
    def load_users(self) -> None:
        '''
        Load users from every course and transform data to convinience format.
        Store users to course's group and self.users.
        '''

        for course in self.courses:

            # Call Moodle API
            course_users = self.get_users(course['id'])

            logger.debug(f'course "{course["title"]}" has {len(course_users)} enrolled.')

            for course_user in course_users:

                user: User = format_user(course_user)

                user_roles = user.pop('roles', None)

                if user['username'] not in self.users:
                    self.users[user['username']] = user

                if user_roles:

                    # Find the most crucial role in a list
                    user['role']: str = self.get_user_highest_role(user_roles)

                    group: str = self.get_user_group(user)

                    course[group].append(user)

    def sync(self, filename: t.Optional[PathLike] = None) -> None:
        '''
        Top-level method to load courses,
        load users from every course,
        transform them, and then
        store them to json file.
        '''

        self.load_courses()

        self.load_users()

        FileWorker(filename).save_json(self.courses)

        logger.info('Successfully update json')

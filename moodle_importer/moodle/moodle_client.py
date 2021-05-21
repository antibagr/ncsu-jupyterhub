import typing as t

from .base import BaseAPIClient
from .response import FluidResponse
from .file_gen import Processor

User = t.Dict[t.Literal['id', 'first_name', 'last_name', 'username', 'email', 'role'], t.Union[str, int]]

Course = t.Dict[t.Literal['id', 'title', 'short_name', 'instructors', 'graders', 'students'], t.Union[str, t.List[User]]]


class MoodleAPI(BaseAPIClient):
    '''Documentation required.'''

    def get_courses(self) -> FluidResponse:

        return self.call('core_course_get_courses')

    def get_users(self, course_id: int) -> FluidResponse:

        return self.call('core_enrol_get_enrolled_users', courseid=course_id)

    def load_courses(self):

        courses = self.get_courses()

        self.c_ids = list(map(lambda x: x['id'], courses))

    def courses_info(self) -> t.List[str]:

        return [f"{c['fullname']} ({c['shortname']}) - {c['id']}" for c in self.get_courses()]

    def list_users(self):

        users = set()

        if not hasattr(self, 'c_ids'):
            self.load_courses()

        for c_id in self.c_ids:

            for user in self.get_users(c_id):

                users.add(user['email'])

        print(users)


class Moodle(MoodleAPI, Processor):

    courses: t.List[Course] = []

    users: t.Dict[str, User] = {}

    def _load_roles(self):

        if hasattr(self, '_roles'):
            raise AttributeError('Roles already created.')

        all_roles = ('student', 'teaching_assistant', 'teacher',
            'instructional_support', 'editingteacher', 'manager', 'coursecreator')
        self._roles = {k: v for k, v in zip(all_roles, range(len(all_roles)))}
        self._roles_reversed = {v: k for k, v in self._roles.items()}

    def priority(self, role: str, reversed: bool = False) -> int:

        if not hasattr(self, '_roles'):
            self._load_roles()

        return self._roles[role] if not reversed else self._roles_reversed[role]


    def _load_courses(self):

        for course in self.get_courses():

            self.courses.append({
                    'id': course['id'],
                    'title': course['displayname'],
                    'short_name': course['shortname'],
                    'instructors': [],
                    'students': [],
                    'graders': [],
                })

    def _load_users(self):

        for course in self.courses:

            course_users = self.get_users(course['id'])

            for user in course_users:

                course_user = {
                    'id': user['id'],
                    'first_name': user['firstname'],
                    'last_name': user['lastname'],
                    'username': user['username'],
                    'email': user['email'],
                }

                if user['email'] not in self.users:
                    self.users[user['email']] = course_user

                if user['roles']:

                    role_rate: int = max([self.priority(role['shortname']) for role in user['roles']])

                    course_user['role']: str = self.priority(role_rate, reversed=True)

                    if course_user['role'] == 'student':
                        group = 'students'
                    elif course_user['role'] in ('editingteacher', 'manager', 'coursecreator'):
                        group = 'instructors'
                    else:
                        group = 'graders'

                    course[group].append(course_user)

    def sync(self):

        print('Loading courses')

        self._load_courses()

        print('Loading users')
        self._load_users()

        self.save_json(self.courses)
        print('Successfully update json')

import typing as t

from .base import BaseAPIClient
from .response import FluidResponse


class Moodle(BaseAPIClient):
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

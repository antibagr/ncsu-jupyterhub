import typing as t

from nbgrader.api import Gradebook

from moodle.helper import MoodleBasicHelper
from moodle.typehints import User
from moodle.utils import grader


class IntegrationHelper(MoodleBasicHelper):
    '''
    Class for storing database connections during adding new students into courses.
    '''

    _dbs: t.Dict[str, Gradebook]

    def __init__(self):
        self._dbs = {}
        super().__init__()

    @staticmethod
    def get_db(course_id: str) -> Gradebook:
        '''
        Create new connection to sqlite database.
        '''

        return Gradebook(f'sqlite:////home/{grader / course_id}/grader.db', course_id=course_id)

    def add_student(self, course_id: str, student: User) -> None:
        '''
        Create or update student in the nbgrader sqlite database.

        Args:
            course_id (str): Course short name.
            student (User): Student to be added.
        '''

        if course_id not in self._dbs:
            self._dbs[course_id] = self.get_db(course_id)

        self._dbs[course_id].update_or_create_student(
            student['username'],
            lms_user_id=student['id'],
            first_name=student['first_name'],
            last_name=student['last_name'],
            email=student['email'],
        )

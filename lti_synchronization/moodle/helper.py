import re
import typing as t

from loguru import logger
from moodle.typehints import Course, JsonType, User
from moodle.utils import JsonDict, grader
from nbgrader.api import Assignment, Gradebook, InvalidEntry
from nbgrader.api import Course as NBCourse
from traitlets.config import LoggingConfigurable


class MoodleBasicHelper(LoggingConfigurable):

    @staticmethod
    def format_string(string: str) -> str:
        '''
        Replace all invalid characters with underscore.

        Args:
            string (str): input string

        Returns:
            str: valid string in lowercase.

        '''

        if not string:
            raise ValueError('string is empty')

        string = re.sub(r'[^\w-]+', '_', string)

        return string.lstrip('_.-').lower()[:50]

    @staticmethod
    def email_to_username(email: str) -> str:
        '''
        Normalizes an email to get a username. This function
        calculates the username by getting the string before the
        @ symbol, removing special characters, removing comments,
        converting string to lowercase, and adds 1 if the username
        has an integer value already in the string.

        Args:
          email: A valid email address

        Returns:
          username: A username string

        Raises:
          ValueError if email is empty
        '''

        if not email:
            raise ValueError('email is missing')

        username = email.split('@')[0]

        username = username.split('+')[0]

        username = re.sub(r'\([^)]*\)', '', username)

        username = re.sub(r'[^\w-]+', '', username)

        username = username.lower()

        logger.debug(f'Normalized email {email!r} to {username!r}')

        return username

    @staticmethod
    def get_user_group(user: User) -> str:

        if user['role'] == 'student':
            group = 'students'
        elif user['role'] in ('editingteacher', 'manager', 'coursecreator', 'instructional_support'):
            group = 'instructors'
        elif user['role'] in ('teaching_assistant', 'teacher'):
            group = 'graders'
        else:
            raise KeyError(user['role'])

        return group

    @staticmethod
    def format_course(course: JsonType) -> Course:
        '''
        Format raw json response to convinient dictionary.
        '''

        return JsonDict({
                'id': course['id'],
                'title': course['displayname'],
                'short_name': course['shortname'],
                'instructors': [],
                'students': [],
                'graders': [],
        })

    @staticmethod
    def format_user(user: JsonType) -> User:
        '''
        Format raw json response to convinient dictionary.
        '''

        return JsonDict({
            'id': user['id'],
            'first_name': user['firstname'],
            'last_name': user['lastname'],
            'username': user['username'],
            'email': user['email'],
            'roles': [role['shortname'] for role in user['roles']],
        })


class NBGraderHelper(MoodleBasicHelper):
    '''
    Class for storing database connections
    during adding new students into courses.
    '''

    _dbs: t.Dict[str, Gradebook]

    def __init__(self):
        self._dbs = {}
        super().__init__()

    @staticmethod
    def _get_db(course_id: str) -> Gradebook:
        '''
        Create new connection to sqlite database.
        '''

        return Gradebook(
            f'sqlite:////home/{grader / course_id}/grader.db',
            course_id=course_id
        )

    def get_db(self, course_id: str) -> Gradebook:
        '''
        Get connection to the course database,
        which will also stored in helper instance.

        Args:
            course_id (str): Normalized course name

        Returns:
            Gradebook: Opened database connection

        '''

        if course_id not in self._dbs:
            self._dbs[course_id] = self._get_db(course_id)

        return self._dbs[course_id]

    def add_student(self, course_id: str, student: User) -> None:
        '''
        Create or update student in the nbgrader sqlite database.

        Args:
            course_id (str): Course short name.
            student (User): Student to be added.
        '''

        with self.get_db(course_id) as gb:

            gb.update_or_create_student(
                student['username'],
                lms_user_id=student['id'],
                first_name=student['first_name'],
                last_name=student['last_name'],
                email=student['email'],
            )

    def update_course(self, course_id: str, **kwargs: t.Any) -> None:
        '''
        Updates the course in nbgrader database
        '''

        with self.get_db(course_id) as gb:
            gb.update_course(course_id, **kwargs)

    def get_course(self, course_id: str) -> NBCourse:
        '''
        Gets the course model instance
        '''

        with self.get_db(course_id) as gb:

            course = gb.check_course(course_id)

            logger.debug(f'course got from db: {course!r}')

            return course

    def register_assignment(
                self,
                course_id: str,
                assignment_name: str,
                **kwargs: t.Any
            ) -> t.Optional[Assignment]:
        '''
        Adds an assignment to nbgrader database

        Args:
            assignment_name: The assingment's name
        Raises:
            InvalidEntry: when there was an error adding the assignment to the database
        '''

        if not assignment_name:
            raise ValueError('assignment_name missing')

        logger.debug(
            'Assignment name normalized %s to save in gradebook' % assignment_name)

        assignment: t.Optional[Assignment] = None

        with self.get_db(course_id) as gb:

            try:
                assignment = gb.update_or_create_assignment(
                    assignment_name, **kwargs)

                logger.debug('Added assignment %s to gradebook' %
                             assignment_name)

            except InvalidEntry as e:

                logger.debug(
                    'Error ocurred by adding assignment to gradebook: %s' % e)

        return assignment

import re
import typing as t

from loguru import logger
from moodle.typehints import Course, JsonType, User
from moodle.utils import JsonDict, grader
from nbgrader.api import Assignment, Gradebook, InvalidEntry
from nbgrader.api import Course as NBCourse
from custom_inherit import DocInheritMeta
# from traitlets.config import LoggingConfigurable


class MoodleBasicHelper(metaclass=DocInheritMeta(
            style='google_with_merge',
            include_special_methods=True
        )):

    @classmethod
    def format_string(cls, string: str) -> str:
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

    @classmethod
    def email_to_username(cls, email: str) -> str:
        '''
        Normalizes an email to get a username. This function
        calculates the username by getting the string before the
        @ symbol, removing special characters, removing comments,
        converting string to lowercase, and adds 1 if the username
        has an integer value already in the string.

        Args:
            email: A valid email address

        Returns:
            str: A username string

        Raises:
          ValueError: if email is empty
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

    @classmethod
    def get_user_group(cls, user: User) -> str:
        '''Map LMS user's role to one of student, instructor or a grader.

        Args:
            user (User): User dict with 'role' key

        Returns:
            str: Jupyterhub role

        Raises:
            KeyError: No appropriate role was found.

        '''

        if user['role'] == 'student':
            group = 'students'
        elif user['role'] in ('editingteacher', 'manager', 'coursecreator', 'instructional_support'):
            group = 'instructors'
        elif user['role'] in ('teaching_assistant', 'teacher'):
            group = 'graders'
        else:
            raise KeyError(user['role'])

        return group

    @classmethod
    def format_course(cls, course: JsonType) -> Course:
        '''Format raw json response to convinient dictionary.

        Args:
            course (JsonType): Raw Json from LMS containing course data.

        Returns:
            Course: JsonDict with course information

        '''

        return JsonDict({
                'id': course['id'],
                'course_id': course['shortname'],
                'title': course['displayname'],
                'category': course['categoryid'],
                'instructors': [],
                'students': [],
                'graders': [],
        })

    @classmethod
    def format_user(cls, user: JsonType) -> User:
        '''Format raw json response to convinient dictionary.

        Args:
            user (JsonType): Raw Json from LMS containing user data.

        Returns:
            User: JsonDict with user information

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

    def _get_db(self, course_id: str) -> Gradebook:
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

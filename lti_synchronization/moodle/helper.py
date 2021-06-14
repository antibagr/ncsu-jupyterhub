import re

from loguru import logger

from traitlets.config import LoggingConfigurable

from moodle.typehints import JsonType, Course, User
from moodle.utils import JsonDict




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

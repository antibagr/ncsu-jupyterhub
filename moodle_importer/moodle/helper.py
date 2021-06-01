import re

from moodle.typehints import JsonType, Course, User
from moodle.utils import JsonDict


class MoodleBasicHelper:

    @staticmethod
    def format_string(string: str) -> str:
        '''
        Replace all invalid characters with underscore.

        Args:
            name (str): input string

        Returns:
            str: valid string in lowercase.

        '''
        return re.sub(r'\W', '_', string.lower())

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

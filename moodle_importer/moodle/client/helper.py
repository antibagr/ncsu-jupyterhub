import typing as t

from moodle.settings import ROLES
from moodle.typehints import JsonType, Course, User


class MoodleDataHelper:
    '''
    Helper for transforming data received from Moodle
    '''

    def __init__(self) -> None:
        '''
        Cache dictionaries with roles.
        '''

        if hasattr(self, '_roles'):
            raise AttributeError('Roles already created.')

        self._roles = dict(list(zip(ROLES, range(len(ROLES)))))
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

    def format_course(self, course: JsonType) -> Course:
        '''
        Format raw json response to convinient dictionary.
        '''

        return {
                'id': course['id'],
                'title': course['displayname'],
                'short_name': course['shortname'],
                'instructors': [],
                'students': [],
                'graders': [],
        }

    def format_user(self, user: JsonType) -> User:
        '''
        Format raw json response to convinient dictionary.
        '''

        return {
            'id': user['id'],
            'first_name': user['firstname'],
            'last_name': user['lastname'],
            'username': user['username'],
            'email': user['email'],
            'roles': [role['shortname'] for role in user['roles']],
        }

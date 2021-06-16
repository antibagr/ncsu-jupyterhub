import typing as t

from moodle.helper import MoodleBasicHelper
from moodle.settings import ROLES
from moodle.typehints import Course, JsonType, User, Role


class MoodleDataHelper(MoodleBasicHelper):
    '''Helper for dealing with a sequence of roles in a User dictionary.

    In Jupyterhub, we don't have strict role separation and full permissions
    functionality. Rather, the nbgrader extensions enabled are defining which
    'role' a user belongs to. Saying so, it's still possible to have a user
    with a grader and student, extensions enabled simultaneously, but it would
    be harder to maintain and track in the future. With that said, we decided
    to support only one role per user, the role with the highest rank
    (i.e. prefer teaching_assistant over student, course creator over
    instructional_support, etc.)
    '''

    def __init__(self) -> None:
        '''
        We transform settings.ROLES tuple into dictionary to
        map every role to its index (position). By doing so, we're allowing
        to easialy (and fast!) find role's position and role name by its
        position reversevely.
        '''

        self._roles = dict(list(zip(ROLES, range(len(ROLES)))))

        self._roles_reversed = {v: k for k, v in self._roles.items()}

    def get_priority(self, role: Role) -> int:
        '''Gets the index of role from settings.ROLES tuple.

        Args:
            role (Role): literal typing.ROLES

        Returns:
            int: index of the role

        Raises:
            KeyError:
                If no such role found. Consider adding it to settings.ROLES

        '''

        return self._roles[role]

    def get_role_name(self, index: int) -> Role:
        '''Gets role name by its index in the settings.ROLES.

        This function is used after role with highest index is found to
        return the name of the role back to User dictionary.

        Args:
            index (int): Index of the highest rank role

        Returns:
            Role: Role name, literal from settings.ROLES
        '''

        return self._roles_reversed[index]

    def find_highest_role(self, roles: t.Sequence[Role]) -> Role:
        '''Finds role with highest rank from the provided roles sequence.

        If the user has multiple course roles (student, TA, for instance)
        it's important to choose the role with the highest priority score
        TA in this example. To find it we determine role with highest score
        (which is an index in the settings.ROLES tuple)

        Args:
            roles (t.Sequence[Role]):
                list or tuple of roles where every role is literal typehints.Role

        Returns:
            Role: name of the highest rank role
        '''

        max_index: int = max(self.get_priority(role) for role in roles)

        # user's highest role name
        return self.get_role_name(max_index)

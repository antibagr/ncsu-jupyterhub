import os
import typing as t
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from moodle import MoodleClient

from moodle.settings import ROLES
from moodle.typehints import User, Course


def test_client_attributes(client: MoodleClient):

    assert hasattr(client, '_roles')
    assert hasattr(client, '_roles_reversed')
    assert tuple(client._roles.keys()) == ROLES

    with pytest.raises(AttributeError):
        client._load_roles()


@pytest.mark.parametrize(
    'roles, expected',
    [
        (['teacher', 'student'], 'teacher'),
        (['student', 'coursecreator', 'teacher'], 'coursecreator'),
        (['editingteacher', 'teacher'], 'editingteacher'),
        (['student', 'teaching_assistant', 'editingteacher'], 'editingteacher'),
        pytest.param([], '', marks=pytest.mark.xfail),
        pytest.param(['student', 'superman'], 'student', marks=pytest.mark.xfail),
    ],
)
def test_client_priority(client: MoodleClient, roles: t.List[str], expected: str):

    assert client.get_user_highest_role(roles) == expected

@pytest.mark.parametrize(
    'test_user, expected',
    [
        ({'role': 'student'}, 'students'),
        ({'role': 'editingteacher'}, 'instructors'),
        ({'role': 'manager'}, 'instructors'),
        ({'role': 'coursecreator'}, 'instructors'),
        ({'role': 'teacher'}, 'graders'),
        ({'role': 'teaching_assistant'}, 'graders'),
        pytest.param({'role': 'superman'}, 'x-men', marks=pytest.mark.xfail),
        pytest.param({}, '', marks=pytest.mark.xfail),
    ],
)
def test_user_group(client: MoodleClient, test_user: dict, expected: str):
    assert client.get_user_group(test_user) == expected


def test_load_courses(client: MoodleClient):

    with patch.object(client, 'call', autospec=True) as mocked_call:

        mocked_call.return_value = range(5)

        with patch('moodle.client.api.format_course') as mocked_format_course:

            client.load_courses()

            mocked_call.assert_called_with('core_course_get_courses')

            assert mocked_format_course.call_count == 5

            assert mocked_format_course.call_args_list == list(map(call, range(5)))


def test_load_users(client: MoodleClient, student: User, teacher: User):

    print(client.courses)

    with patch.object(client, 'get_courses', autospec=True) as mocked_get_courses:

        with patch.object(client, 'get_users', autospec=True) as mocked_get_users:

            mocked_get_users.return_value = [student, teacher]

            with patch('moodle.client.api.format_user', new=lambda user: user.copy()):

                client.load_users()

                print(client.courses)
                print(client.users)

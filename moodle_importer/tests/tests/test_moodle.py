import os
import typing as t
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from moodle.client.api import MoodleClient
from moodle.client.helper import MoodleDataHelper
from moodle.settings import ROLES
from moodle.typehints import Course, User


def test_helper(helper: MoodleDataHelper):

    assert hasattr(helper, '_roles')
    assert hasattr(helper, '_roles_reversed')
    assert tuple(helper._roles.keys()) == ROLES

    with pytest.raises(AttributeError):
        helper._load_roles()


@pytest.mark.parametrize(
    'roles, expected',
    [
        (['teacher', 'student'], 'teacher'),
        (['student', 'coursecreator', 'teacher'], 'coursecreator'),
        (['editingteacher', 'teacher'], 'editingteacher'),
        (['student', 'teaching_assistant', 'editingteacher'], 'editingteacher'),
        pytest.param([], '', marks=pytest.mark.xfail),
        pytest.param(['student', 'superman'], 'student',
                     marks=pytest.mark.xfail),
    ],
)
def test_priority(helper: MoodleDataHelper, roles: t.List[str], expected: str):

    assert helper.get_user_highest_role(roles) == expected


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
def test_user_group(helper: MoodleDataHelper, test_user: dict, expected: str):
    assert helper.get_user_group(test_user) == expected


def test_load_courses(client: MoodleClient):

    with patch.object(client, 'call', autospec=True) as mocked_call:

        mocked_call.return_value = range(5)

        with patch.object(client.helper, 'format_course', autospec=True) as mocked_format_course:

            client.load_courses()

            mocked_call.assert_called_with('core_course_get_courses')

            assert mocked_format_course.call_count == 5

            assert mocked_format_course.call_args_list == list(
                map(call, range(5)))


def test_load_users(client: MoodleClient, student: User, teacher: User, course: Course):
    '''
    Test transforming data process.
    '''

    # reset groups
    course['graders'] = []
    course['instructors'] = []
    course['students'] = []

    client.courses = [course, ]

    # we have teacher and two repeated students.
    with patch.object(client, 'get_users', return_value=[student, student, teacher]) as mocked_get_users:

        with patch.object(client.helper, 'format_user', new=lambda user: user.copy()):

            client.load_users()

            # do the same work client does with users
            # to compare data
            student['role'] = student.pop('roles')[0]
            teacher['role'] = teacher.pop('roles')[0]

            mocked_get_users.assert_called_once_with(course['id'])

            assert client.courses == [
                {**course, 'graders': [teacher],
                    'students': [student, student]}
            ]

            assert client.users == {
                teacher['username']: teacher, student['username']: student}


@pytest.mark.smoke
def test_call_real_api(client: MoodleClient):

    with patch('moodle.client.api.FileWorker.save_json') as mocked_json:

        client.sync()

        mocked_json.assert_called_once_with(client.courses)

import os
import typing as t
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from moodle.client.api import MoodleClient
from moodle.client.helper import MoodleDataHelper
from moodle.settings import ROLES
from moodle.typehints import Course, User
from moodle.utils import JsonDict
from tests.typehints import MonkeyPatch


fail = pytest.mark.xfail


@pytest.fixture
def setenv_category(monkeypatch: MonkeyPatch) -> t.Callable:

    def _setenv_category(a: str, b: str) -> None:

        monkeypatch.setenv('MOODLE_JUPYTERHUB_CATEGORY_ID', a)
        monkeypatch.setenv('MOODLE_NBGRADER_CATEGORY_ID', b)

    return _setenv_category


def test_helper(helper: MoodleDataHelper):
    '''
    It's very important for helper to use ROLES from settings.
    '''

    assert hasattr(helper, '_roles')
    assert hasattr(helper, '_roles_reversed')
    assert tuple(helper._roles.keys()) == ROLES


@pytest.mark.parametrize(
    'roles, expected',
    [
        (['teacher', 'student'], 'teacher'),
        (['student', 'coursecreator', 'teacher'], 'coursecreator'),
        (['editingteacher', 'teacher'], 'editingteacher'),
        (['student', 'teaching_assistant', 'editingteacher'], 'editingteacher'),
        pytest.param([], '', marks=fail),
        pytest.param(['student', 'superman'], 'student', marks=fail),
    ],
)
def test_priority(helper: MoodleDataHelper, roles: t.List[str], expected: str):

    assert helper.find_highest_role(roles) == expected


@pytest.mark.parametrize(
    'test_user, expected',
    [
        ({'role': 'student'}, 'students'),
        ({'role': 'editingteacher'}, 'instructors'),
        ({'role': 'manager'}, 'instructors'),
        ({'role': 'coursecreator'}, 'instructors'),
        ({'role': 'teacher'}, 'graders'),
        ({'role': 'teaching_assistant'}, 'graders'),
        pytest.param({'role': 'superman'}, 'x-men', marks=fail),
        pytest.param({}, '', marks=fail),
    ],
)
def test_user_group(helper: MoodleDataHelper, test_user: dict, expected: str):
    '''
    Test getting group for various roles.
    '''

    assert helper.get_user_group(test_user) == expected


def test_load_courses(client: MoodleClient):

    with patch.object(client, 'call', autospec=True) as mocked_call:

        mocked_call.return_value = range(5)

        with patch.object(client.helper, 'format_course', autospec=True) as mock_format:

            client.load_courses()

            mocked_call.assert_called_with('core_course_get_courses')

            assert mock_format.call_count == 5

            assert mock_format.call_args_list == list(map(call, range(5)))


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
    with patch.object(client, '_get_users') as mocked_get_users:

        mocked_get_users.return_value = [
            JsonDict(u) for u in (student, student, teacher)]

        client.load_users()

        # do the same work client does with users
        # to compare data
        student.role = student.pop('roles')[0]
        teacher.role = teacher.pop('roles')[0]

        mocked_get_users.assert_called_once_with(course)

        assert client.courses == [{
                **course,
                'graders': [teacher],
                'students': [student, student]
            }]

        assert client.users == {
            teacher.username: teacher, student.username: student}


@pytest.mark.smoke
def test_call_real_api(client: MoodleClient):

    with patch('moodle.client.api.FileWorker.save_json') as mocked_json:

        client.sync()

        mocked_json.assert_called_once_with(client.courses)


def test_use_category_env(get_client: t.Callable[[], MoodleClient], setenv_category: t.Callable):
    '''
    Does the client track environment variables state?
    Does it continuously check environment variables even after
    the property set to True?
    Will it be fine to pass non-numeric values?
    '''

    setenv_category('', '')

    with pytest.raises(EnvironmentError):
        get_client().use_categories()

    setenv_category('foo', 'bar')

    with pytest.raises(ValueError):
        get_client().use_categories()

    with patch('moodle.client.api.os.getenv') as mock_getenv:

        client = get_client()

        client._use_categories = True

        client.use_categories()

        mock_getenv.assert_not_called()

    setenv_category('1', '2')

    client = get_client()

    client.use_categories()

    assert client._cats == (1, 2)


def test_get_categories(client: MoodleClient):
    '''
    Does get categories returns courses in valid format?
    '''

    courses = [JsonDict(title='Foo Course',
                        course_id='foo_course',
                        category=1)]

    with patch.object(client, '_get_courses', return_value=[]) as get_course:

        assert client.get_categories() == []

        get_course.return_value = courses

        assert client.get_categories() == [('Foo Course', 'foo_course', 1)]


def test_filter_courses(client: MoodleClient):

    with patch.object(client, '_get_courses') as get_courses:

        courses = get_courses.return_value = [
            JsonDict(course_id='foo_course'),
            JsonDict(course_id='bar_course'),
        ]

        client.load_courses(course_id='foo_course')

        assert client.courses == courses[:1]

        # Filtering with multiple options

        courses = get_courses.return_value = [
            JsonDict(course_id='foo'),
            JsonDict(course_id='bar'),
            JsonDict(course_id='egg'),
            JsonDict(course_id='baz'),
        ]

        for seq in (list, tuple, set, frozenset):

            client.courses = []

            client.load_courses(course_id=seq(('foo', 'bar')))

            assert client.courses == courses[:2]

        # Filtering by multiple fields

        courses = get_courses.return_value = [
            JsonDict(title='The Foo', course_id='baz'),
            JsonDict(title='The Bar', course_id='baz'),
            JsonDict(title='The Spam', course_id='spam'),
        ]

        client.courses = []

        client.load_courses(title=('The Foo', 'The Spam'), course_id='baz')

        assert client.courses == [courses[0]]

        # Empty sequence is not allowed
        with pytest.raises(ValueError):
            client.load_courses(title=(), course_id='baz')

        # Invalid key for the course
        with pytest.raises(KeyError):
            client.load_courses(foo='bar')


def test_filter_categories(client: MoodleClient, setenv_category: t.Callable):
    '''
    Does client mix well categories filtering and filters keywords?
    '''

    setenv_category('1', '2')

    with patch.object(client, '_get_courses') as get_courses:

        courses = get_courses.return_value = [
            JsonDict(course_id='foo', category=1),
            JsonDict(course_id='bar', category=2),
            JsonDict(course_id='baz', category=5),
            JsonDict(course_id='spam', category=10),
        ]

        client.use_categories()

        client.load_courses()

        assert client.courses == courses[:2]

        client.courses = []

        client.load_courses(course_id='foo')

        assert client.courses == courses[:1]

        client.courses = []

        client.load_courses(course_id=('spam', 'baz'))

        assert client.courses == []

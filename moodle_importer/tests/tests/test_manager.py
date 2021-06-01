import typing as t
import pytest
from unittest import mock

from moodle.integration.helper import IntegrationHelper
from moodle.integration.system import SystemCommand
from moodle.integration.template import Templater
from moodle.typehints import User


@pytest.fixture
def system():
    return SystemCommand()


def test_helper(student: User):

    helper = IntegrationHelper()

    with mock.patch('moodle.integration.helper.Gradebook') as mocked_gradebook:

        mocked_gradebook.update_or_create_student = mock.Mock()

        helper.add_student('course_id', student)

        assert 'course_id' in helper._dbs

        mocked_gradebook.assert_called_once_with('sqlite:////home/grader-course_id/grader.db', course_id='course_id')

        mocked_gradebook().update_or_create_student.assert_called_once_with(
            student['username'],
            lms_user_id=student['id'],
            first_name=student['first_name'],
            last_name=student['last_name'],
            email=student['email'],
        )

@pytest.mark.parametrize('dirs, line', [
    (['one'], 'mkdir -p one'),
    (['one', 'two'], 'mkdir -p one two'),
    ([['one', 'two']], 'mkdir -p one two'),
    (('one', 'two'), 'mkdir -p one two'),
    ((('one', 'two')), 'mkdir -p one two'),
    pytest.param([], '', marks=pytest.mark.xfail),
    pytest.param((), '', marks=pytest.mark.xfail),
    pytest.param([object(), [], {}], '', marks=pytest.mark.xfail),
])
@mock.patch('moodle.integration.system.os.system')
def test_system_create_dirs(mocked_os: mock.MagicMock, system: SystemCommand, dirs: t.Any, line: str):

    system.create_dirs(*dirs)
    mocked_os.assert_called_once_with(line)


@mock.patch('moodle.integration.system.os.system')
def test_system_create_db(mocked_os: mock.MagicMock, system: SystemCommand):

    system.create_database('grader')

    mocked_os.assert_has_calls([
        mock.call('touch /home/grader/grader.db'),
        mock.call('chown -R grader:grader /home/grader/grader.db'),
        mock.call('chmod 644 /home/grader/grader.db'),
    ])

@mock.patch('moodle.integration.template.open', new_callable=mock.mock_open)
def test_templater_write_config(mocked_open: mock.MagicMock):

    Templater.write_grader_config('test_course')

    mocked_open.assert_any_call('/home/grader-test_course/.jupyter/nbgrader_config.py', 'w')
    mocked_open.assert_any_call('/home/grader-test_course/test_course/nbgrader_config.py', 'w')

    assert mocked_open().write.call_count == 2


def test_templater_new_service():

    service = Templater.create_service('test_course', 'token')

    assert tuple(service.keys()) == ('name', 'admin', 'url', 'command', 'user', 'cwd', 'api_token', 'environment')

    assert service.admin is True
    assert service.name == 'test_course'
    assert service.api_token == 'token'
    assert service.url == 'http://127.0.0.1:9000'

    with pytest.raises(TypeError):
        Templater.create_service('test_course', 'token', 'invalid_port')

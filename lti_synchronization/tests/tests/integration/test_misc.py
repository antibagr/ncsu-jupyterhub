import os
import typing as t
from pathlib import Path
from unittest import mock

import pytest

from moodle.helper import NBGraderHelper
from moodle.integration.system import join_dirs, create_dirs, create_database, chown
from moodle.integration.template import Templater
from moodle.typehints import User


@pytest.fixture
def gradebook() -> t.Tuple[mock.Mock, mock.Mock]:
    '''Mocks nbgrader Gradebook.

    Returns:
        t.Tuple[mock.Mock, mock.Mock]:
            gradebook type which would be called to instantiate new gradebook
            and gradebook instance as second mock.

    '''

    with mock.patch('moodle.helper.Gradebook') as gb_type:

        gb_inst = mock.Mock()

        gb_type.return_value.__enter__.return_value = gb_inst

        yield (gb_type, gb_inst)


def test_helper_add_student(student: User, gradebook: t.Tuple[mock.Mock, mock.Mock]):
    '''
    Does helper open correct database when adding new student to a course?
    '''

    gb_type, gb_inst = gradebook

    helper = NBGraderHelper()

    helper.add_student('foo_course', student)

    assert 'foo_course' in helper._dbs

    gb_type.assert_called_once_with(
        'sqlite:////home/grader-foo_course/grader.db',
        course_id='foo_course'
    )

    gb_inst.update_or_create_student.assert_called_once_with(
        student['username'],
        lms_user_id=student['id'],
        first_name=student['first_name'],
        last_name=student['last_name'],
        email=student['email'],
    )


def test_helper_get_db():
    '''
    Does helper manage databases correctly?
    '''

    helper = NBGraderHelper()

    with mock.patch.object(helper, '_get_db') as mock_get_db:

        helper.get_db('foo_course')
        helper.get_db('foo_course')
        helper.get_db('bar_course')
        helper.get_db('foo_course')

        mock_get_db.assert_has_calls((
            mock.call('foo_course'),
            mock.call('bar_course'),
        ))


@pytest.mark.parametrize('dirs, line', [
    (['one'], 'mkdir -p one'),
    (['one', 'two'], 'mkdir -p one two'),
    ([['one', 'two', 'three']], 'mkdir -p one two three'),
    (('one', 'two'), 'mkdir -p one two'),
    ((('one', 'two')), 'mkdir -p one two'),
    pytest.param([], '', marks=pytest.mark.xfail),
    pytest.param((), '', marks=pytest.mark.xfail),
    pytest.param([object(), [], {}], '', marks=pytest.mark.xfail),
])
@mock.patch('moodle.integration.system.os.system')
def test_system_create_dirs(mocked_os: mock.MagicMock, dirs: t.Any, line: str):

    create_dirs(*dirs)
    mocked_os.assert_called_once_with(line)


def test_join_dirs():
    '''
    Does join_dirs function raise necessary exceptions and handle
    input mixed type input properly?
    '''

    with pytest.raises(ValueError):

        join_dirs(None)

    with pytest.raises(ValueError):

        join_dirs(('', ))

    with pytest.raises(TypeError):
        join_dirs('string dir', Path('path dir'), bytes())

    res = join_dirs(('dir1', 'dir2', Path('dir3'), os.path.join('a', 'b')))

    assert res == 'dir1 dir2 dir3 a{}b'.format(os.path.sep)


def test_low_level_system_api():

    with pytest.raises(ValueError):
        chown('', ['dir'])

    with pytest.raises(ValueError):
        chown('user', ['dir'], group='')


@mock.patch('moodle.integration.system.os.system')
def test_system_create_db(mocked_os: mock.MagicMock):

    create_database('grader')

    mocked_os.assert_has_calls([
        mock.call('touch /home/grader/grader.db'),
        mock.call('chown -R grader:grader /home/grader/grader.db'),
        mock.call('chmod 644 /home/grader/grader.db'),
    ])


@mock.patch('moodle.integration.template.open', new_callable=mock.mock_open)
def test_templater_write_config(mocked_open: mock.MagicMock):

    Templater.write_grader_config('test_course')

    config_path = '/home/grader-test_course/{}/nbgrader_config.py'

    mocked_open.assert_any_call(config_path.format('.jupyter'), 'w')
    mocked_open.assert_any_call(config_path.format('test_course'), 'w')

    assert mocked_open().write.call_count == 2


def test_templater_new_service():

    service = Templater.create_service('test_course', 'token')

    assert tuple(service.keys()) == ('name', 'admin', 'url', 'command', 'user',
                                     'cwd', 'api_token', 'environment')

    assert service.admin is True
    assert service.name == 'test_course'
    assert service.api_token == 'token'
    assert service.url == 'http://127.0.0.1:9000'

    with pytest.raises(TypeError):
        Templater.create_service('test_course', 'token', 'invalid_port')

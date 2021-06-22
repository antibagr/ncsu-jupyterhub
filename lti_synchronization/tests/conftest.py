import asyncio
import random
import re
import string
import typing as t

import pytest
from dotenv import load_dotenv

from moodle.client.api import MoodleClient
from moodle.client.helper import MoodleDataHelper
from moodle.settings import ROLES
from moodle.typehints import Course, Role, User
from moodle.utils import JsonDict


def pytest_sessionfinish(*_):
    asyncio.get_event_loop().close()

def pytest_sessionstart(session):
    load_dotenv()


def valid_email(email: str) -> bool:
    '''
    Check if email is valid with regex.
    '''
    return bool(re.search(r'^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$', email))


def random_string(length: int = 10) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def make_roles(*role_names: str) -> t.List[Role]:
    return [{'shortname': name} for name in role_names]


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture
def get_client() -> t.Callable[[], MoodleClient]:

    def _get_client(*args, **kwargs) -> MoodleClient:
        return MoodleClient(*args, **kwargs)

    return _get_client


@pytest.fixture
def client(get_client) -> MoodleClient:
    '''
    Instantiated client with dev server credentials.
    '''
    return get_client()


@pytest.fixture
def helper() -> MoodleDataHelper:
    return MoodleDataHelper()


@pytest.fixture
def user_fabric() -> t.Callable[[t.Any, ...], User]:
    '''
    User fabric decorator.
    '''

    def _user_fabric(*,
                     id: t.Optional[int] = None,
                     username: t.Optional[str] = None,
                     email: t.Optional[str] = None,
                     first_name: t.Optional[str] = None,
                     last_name: t.Optional[str] = None,
                     roles: t.Optional[t.List[Role]] = None,
                     ) -> User:
        '''
        Create new user. Keyword-only arguments allowed.
        '''

        if id and not isinstance(id, int):
            raise TypeError('User id must be int.')

        if email and not valid_email(email):
            raise ValueError('Invalid email: %s' % email)

        if username and re.findall(r'\W+', username):
            raise ValueError(
                'Username contains invalid characters: %s' % username)

        if roles:
            for role in roles:
                if role not in ROLES:
                    raise ValueError(
                        'Role [%s] does not set in moodle.setitngs.ROLES tuple.' % role)

        return JsonDict({
            'id': id or random.randint(0, 100),
            'username': username or random_string(10),
            'email': email or f'{random_string(10)}@mail.com',
            'first_name': first_name or random_string(10),
            'last_name': last_name or random_string(10),
            'roles': roles or [random.choice(ROLES) for _ in range(random.randint(0, 5))],
        })
    return _user_fabric


@pytest.fixture
def course_fabric(user_fabric: t.Callable) -> t.Callable[[t.Any, ...], Course]:
    '''
    Course fabric decorator.
    '''

    def _course_fabric(*,
                       id: t.Optional[int] = None,
                       title: t.Optional[str] = None,
                       course_id: t.Optional[str] = None,
                       category: t.Optional[int] = None,
                       instructors: t.Optional[t.List[User]] = None,
                       students: t.Optional[t.List[User]] = None,
                       graders: t.Optional[t.List[User]] = None,
                       ) -> Course:
        '''
        Create new course. Keyword-only arguments allowed.
        '''

        if id and not isinstance(id, int):
            raise TypeError('User id must be int.')

        if course_id and re.findall(r'\W+', course_id):
            raise ValueError(
                'Short name contains invalid characters: %s' % course_id)

        # Python does strange things
        # with lists in default values ...
        instructors = instructors or []
        students = students or []
        graders = graders or []

        for user in instructors + students + graders:
            assert tuple(user.keys()) == ('id', 'username',
                                          'email', 'first_name', 'last_name', 'roles')

        return JsonDict({
            'id': id or random.randint(1, 100),
            'title': title or random_string(20),
            'course_id': course_id or random_string(20),
            'category': category or random.randint(0, 100),
            'instructors': [] or [user_fabric() for _ in range(random.randint(0, 5))],
            'students': [] or [user_fabric() for _ in range(random.randint(0, 5))],
            'graders': [] or [user_fabric() for _ in range(random.randint(0, 5))],
        })
    return _course_fabric


@pytest.fixture
def student(user_fabric: t.Callable) -> User:
    return user_fabric(
        **{
            'email': 'plato@mail.com',
            'first_name': 'Plato',
            'id': 427,
            'last_name': '',
            'roles': ['student'],
            'username': 'plato'
        }
    )


@pytest.fixture
def teacher(user_fabric: t.Callable) -> User:
    return user_fabric(
        **{
            'email': 'socrates@mail.com',
            'first_name': 'Socrates',
            'id': 470,
            'last_name': '',
            'roles': ['teacher'],
            'username': 'socrates'
        }
    )


@pytest.fixture
def course(course_fabric: t.Callable, student: User, teacher: User) -> Course:
    return course_fabric(
        students=[student],
        graders=[teacher]
    )

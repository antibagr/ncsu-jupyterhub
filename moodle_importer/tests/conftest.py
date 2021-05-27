import re
import pytest
import typing as t
import random
import string

from moodle import MoodleClient
from moodle.typehints import Course, User, Role
from moodle.settings import ROLES


def valid_email(email: str) -> bool:
    '''
    Check if email is valid with regex.
    '''
    return bool(re.search(r'^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$', email))


def random_string(length: int = 10) -> str:
     return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def make_roles(*role_names: str) -> t.List[Role]:
    return [{'shortname': name} for name in role_names]


@pytest.fixture(scope='function')
def client() -> MoodleClient:
    '''
    Instantiated client with dev server credentials.
    '''
    return MoodleClient('https://rudie.moodlecloud.com', '0461b4a7e65e63921172fa3727f0863c')


@pytest.fixture
def user_fabric() -> t.Callable[[t.Union[str, int, t.List[Role]]], User]:
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
            raise ValueError('Username contains invalid characters: %s' % username)

        if roles:
            for role in roles:
                if role not in ROLES:
                    raise ValueError('Role [%s] does not set in moodle.setitngs.ROLES tuple.' % role)

        return {
            'id': id or random.randint(0, 100),
            'username': username or random_string(10),
            'email': email or f'{random_string(10)}@mail.com',
            'first_name': first_name or random_string(10),
            'last_name': last_name or random_string(10),
            'roles': roles or [random.choice(ROLES) for _ in range(random.randint(0, 5))],
        }
    return _user_fabric


@pytest.fixture
def course_fabric(user_fabric: t.Callable) -> t.Callable[[t.Union[str, int, t.List[User]]], Course]:
    '''
    Course fabric decorator.
    '''

    def _course_fabric(*,
        id: t.Optional[int] = None,
        title: t.Optional[str] = None,
        short_name: t.Optional[str] = None,
        instructors: t.Optional[t.List[User]] = None,
        students: t.Optional[t.List[User]] = None,
        graders: t.Optional[t.List[User]] = None,
    ) -> Course:
        '''
        Create new course. Keyword-only arguments allowed.
        '''

        if id and not isinstance(id, int):
            raise TypeError('User id must be int.')

        if short_name and re.findall(r'\W+', short_name):
            raise ValueError('Short name contains invalid characters: %s' % short_name)

        # Python does strange things
        # with lists in default values ...
        instructors = instructors or []
        students = students  or []
        graders = graders or []

        for user in instructors + students + graders:
            assert tuple(user.keys()) == ('id', 'username', 'email', 'first_name', 'last_name', 'roles')

        return {
            'id': id or random.randint(1, 100),
            'title': title or random_string(20),
            'short_name': short_name or random_string(20),
            'instructors': [] or [user_fabric() or _ in range(random.randint(0, 5))],
            'students': [] or [user_fabric() or _ in range(random.randint(0, 5))],
            'graders': [] or [user_fabric() or _ in range(random.randint(0, 5))],
        }
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

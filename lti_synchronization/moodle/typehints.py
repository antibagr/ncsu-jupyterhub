'''
Typing aliases used in the moodle package.
Previously it was defined as real typing aliases, like this one:

User = Dict[Literal['id', 'first_name', 'last_name', 'username', 'email', 'role'], Union[str, int, Role]]

But it turns out that Sphinx 'unpack' variables in generated documentation,
so we see full Dict[Literal[...]] instead of simply 'User' as in the source code

We decided then to transform these type aliases into string to improve docs
readability. Obvious disatvantage of this decicion is we could not use type
checker on these anymore, but it could be fixed with some dynamic assignment::

if os.getenv('MAKING_DOCUMENTATION'):
    User = 'User'
else:
    User = User = Dict[Literal[...], Union[...]]

'''
import os
import pathlib
import typing as t

from .settings import ROLES


Serializable = t.Union[str, int, float, bool, None]

JsonContent = 'JsonContent'
'''
Alias for Union[Serializable, List[Serializable], Tuple[Serializable, ...], MutableMapping[str, Serializable]]
'''

Json = 'Json'
''' Alias for t.MutableMapping[t.Hashable, JsonContent] '''

JsonType = 'JsonType'
''' Alias for t.Union[Json, t.Sequence[Json]] '''

PathLike = t.Union[str, pathlib.Path, os.PathLike]

Role = t.Literal['foo']
'''
Literal for roles strings available at settings.ROLES
'''

# We generate Literal dynamically
Role.__args__ = ROLES

User = 'User'
'''Alias for

Dict[Literal['id', 'first_name', 'last_name', 'username', 'email', 'role'], Union[str, int, Role]]
'''

Course = 'Course'
'''Alias for

Dict[Literal['id', 'title', 'short_name', 'instructors', 'graders', 'students'], Union[str, List[User]]]
'''


ByteParams = 'ByteParams'
'''
Alias for Dict[Hashable, List[bytes]]
'''

Dirs = t.Tuple[PathLike, ...]
'''
Tuple of PathLike objects
'''

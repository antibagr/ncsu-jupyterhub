import os
import pathlib
import typing as t

from moodle.settings import ROLES

''' Typing Hints '''

Serializable = t.Union[str, int, float, bool, None]

JsonContent = t.Union[
    Serializable,
    t.List[Serializable],
    t.Tuple[Serializable, ...],
    t.MutableMapping[str, Serializable],
]

Json = t.MutableMapping[str, JsonContent]

JsonType = t.Union[Json, t.Sequence[Json]]

PathLike = t.TypeVar("PathLike", str, pathlib.Path, os.PathLike)

Role = t.Literal['foo']

# We generate Literal dynamically
Role.__args__ = ROLES

User = t.Dict[t.Literal['id', 'first_name', 'last_name',
                        'username', 'email', 'role'], t.Union[str, int, Role]]

Course = t.Dict[t.Literal['id', 'title', 'short_name',
                          'instructors', 'graders', 'students'], t.Union[str, t.List[User]]]

import os
import pathlib

import typing as t

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

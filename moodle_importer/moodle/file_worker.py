import json
import typing as t
from pathlib import Path

from moodle.typehints import JsonType, PathLike
from moodle.utils import dump_json
from moodle.settings import JSON_FILE


class FileWorker(object):

    def __init__(self, filename: t.Optional[PathLike] = None):
        self._filename = filename or JSON_FILE

    @property
    def filename(self) -> PathLike:
        return self._filename

    @filename.setter
    def filename_setter(self, filename: PathLike) -> None:
        self._filename = filename

    def save_json(self, data: str) -> None:
        with open(self.filename, 'w') as f:
            f.write(dump_json(data))

    def load_json(self) -> JsonType:
        with open(self.filename, 'r') as f:
            return json.loads(f.read())

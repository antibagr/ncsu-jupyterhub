import typing as t
from pathlib import Path
import json

from moodle.typehints import PathLike, JsonType
from moodle.utils import dump_json



class Processor(object):

    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    FILE_NAME: str = 'courses.json'

    _filename: PathLike = BASE_DIR / 'data' / FILE_NAME

    @property
    def filename(self) -> PathLike:
        return self._filename

    @filename.setter
    def filename_setter(self, filename: PathLike) -> None:
        self._filename = filename

    def save_json(self, data: str) -> None:
        with open(self.filename, 'w') as f:
            f.write(dump_json(data))

    def load_json(self, filename: t.Optional[PathLike] = None) -> JsonType:
        with open(filename or self.filename, 'r') as f:
            return json.loads(f.read())

''' Function utils '''

import json
import typing as t
from functools import wraps

from loguru import logger

from .settings import JSON_FILE
from .typehints import JsonType, PathLike


def dump_json(dict_in: JsonType) -> str:
    '''
    Dump json-like dictionary to string with indentation.
    '''

    return json.dumps(dict_in, indent=4, sort_keys=True, ensure_ascii=False)


def log_load_data(attr_name: str) -> t.Callable:
    '''
    Assume a func will store downloaded data to attr_name attribute,
    and we're able to get it's length.
    '''

    def _load_data(func: t.Callable) -> t.Callable:

        @wraps(func)
        def wrapper(self, *args: t.Any, **kw: t.Any) -> t.Any:

            logger.info(f'Loading {attr_name} ...')

            result = func(self, *args, **kw)

            logger.info(f'Loaded {len(getattr(self, attr_name))} {attr_name}.')

            return result
        return wrapper
    return _load_data


class Grader(int):
    '''
    Overload division method.
    To create a grader name simply use division:

    Examples:

        Use with course id::

            >>> grader / 'test_course'
            >>> 'grader-test_course'
    '''

    @staticmethod
    def __truediv__(course_id: str) -> str:

        if not isinstance(course_id, str):
            raise TypeError('provide course id to generate grader name.')

        return f'grader-{course_id}'


grader = Grader()


class JsonDict(dict):
    '''Javascript-style json. You can access values in dict as dict's attributes.

    Examples:

        You can access keys like instance's properties::

            new_json = JsonDict(key='value')
            new_json.key
            >>> 'value'

        You can set keys as properties::

            new_json.key = 'something new'
            new_json
            >>> {'key': 'something new'}

        Finally, it's allowed to delete attributes to remove appropriate keys::

            del new_json.key
            new_json
            >>> {}

    '''

    def __getattr__(self, key: t.Hashable) -> t.Any:
        try:
            return self[key]
        except KeyError as err:
            raise AttributeError(key) from err

    def __setattr__(self, key: t.Hashable, value: t.Any) -> None:
        self[key] = value

    def __delattr__(self, key: t.Hashable) -> None:

        if key in self:
            del self[key]
        else:
            super().__delattr__(str(key))


def save_moodle_courses(courses: JsonType, filename: t.Optional[PathLike] = None) -> None:
    '''Saves downloaded formatted courses to a json file.

    To make lti_synchronization package more configurable, we added two ways of
    synchronize data between Jupyterhub and Moodle. You can call synchronize
    function from the package or use MoodleClient and SyncManager separately.

    If you would like just to store courses somewhere so you can modify or inspect
    the data you receive from Moodle, this function would call to create json file.

    Args:
        data (JsonType): Data to be saved in json.
        filename (t.Optional[PathLike]): Path to json file. Defaults to None.
    '''

    with open(filename or JSON_FILE, 'w') as f:

        f.write(dump_json(courses))


def load_moodle_courses(filename: t.Optional[PathLike] = None) -> JsonType:
    '''Loads courses that were saved into a json file.

    Note:
        Does not transform courses into JsonDict instance, rather returns
        regular json instance.

    Args:
        filename (t.Optional[PathLike]): Path to json file. Defaults to None.

    Returns:
        JsonType: Courses from the json file.

    '''

    with open(filename or JSON_FILE, 'r') as f:

        return json.loads(f.read())

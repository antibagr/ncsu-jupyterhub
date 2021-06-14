import json
import typing as t
from functools import wraps

from loguru import logger
from moodle.typehints import Course, JsonType, User

''' Function utils '''


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

    grader / 'test_course'
    >>> 'grader-test_course'
    '''

    @staticmethod
    def __truediv__(course_id: str) -> str:
        assert isinstance(
            course_id, str), 'provide course id to generate grader name.'
        return f'grader-{course_id}'


grader = Grader()


class JsonDict(dict):
    '''
    Javascript-style json
    You can access values in dict as dict's attributes.

    new_json = JsonDict(key='value')
    new_json.key
    >>> 'value'

    new_json.key = 'something new'
    new_json
    >>> {'key': 'something new'}

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

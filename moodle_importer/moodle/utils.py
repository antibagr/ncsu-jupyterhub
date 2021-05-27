import typing as t
import json
from functools import wraps

from loguru import logger

from moodle.typehints import JsonType, Course, User

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

import json

from .typehints import JsonType

''' Function utils '''


def dump_json(dict_in: JsonType) -> str:
    '''
    Dump json-like dictionary to string with indentation.
    '''

    return json.dumps(dict_in, indent=4, sort_keys=True, ensure_ascii=False)

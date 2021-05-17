import typing as t
import json


def dump_json(dict_in: t.Dict) -> str:
    '''
    Dump json-like dictionary to string with indentation.
    '''
    return json.dumps(dict_in, indent=4, sort_keys=True)

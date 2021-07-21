import json
import typing as t
from unittest import mock

from dotenv import load_dotenv

from .client.api import MoodleClient
from .integration.manager import SyncManager
from .typehints import PathLike, Filters
from .utils import dump_json


def synchronize(
    *,
    json_in: t.Optional[PathLike] = None,
    json_out: t.Optional[PathLike] = None,
    in_file: t.Optional[PathLike] = None,
    out_file: t.Optional[PathLike] = None,
    url: t.Optional[str] = None,
    key: t.Optional[str] = None,
    endpoint: t.Optional[str] = None,
    url_env_name: t.Optional[str] = None,
    key_env_name: t.Optional[str] = None,
    **filters: Filters,
) -> None:
    '''Short summary.

    Args:
        use_categories (bool):
            Forces the client to filter courses by category. Defaults to True.
        save_on_disk (bool):
            If set to False, courses will not be saved to json file.
            Defaults to True.
        json_path (t.Optional[PathLike]):
            Path to json file to be used over the default. Defaults to None.
        in_file (t.Optional[PathLike]):
            template file path if it differs from default. Defaults to None
        out_file (t.Optional[PathLike]):
            jupyterhub_config location if it differs from default. Defaults to None.
        url (:obj:`str`, optional):
            Moodle domain name. Defaults to None.
        key (:obj:`str`, optional):
            Moodle web service token. Defaults to None.
        endpoint (:obj:`str`, optional):
            Custom endpoint. Defaults to None.
        url_env_name (:obj:`str`, optional):
            Custom environment variable name for url. Defaults to None.
        key_env_name (:obj:`str`, optional):
            Custom environment variable name for api token. Defaults to None.
        **filters (Filters):
            key-value pairs where value can be both single value or list
            of valid items.
    '''

    load_dotenv(verbose=True)

    keys = ('jupyterhub', 'nbgrader')

    with open(json_in, 'r') as f:
        json_in_file = json.loads(f.read())

        if set(keys) != json_in_file.keys():
            raise KeyError(
                f'Your input JSON does not have required keys: {keys}. '
                'Please consider reading about using filters.'
                )

        for key in keys:
            if not isinstance(json_in_file[key], list):
                raise TypeError(
                    f'Your input JSON must contain keys: {keys}.'
                    '\nEach of them supposed to be an array of courses\' ids.'
                    f'''\nExample:\n\n{dump_json({
                        'jupyterhub': ['course_one', 'course_two'],
                        'nbgrader': ['course_three', 'course_four']
                    })}'''
                )

            for val in json_in_file[key]:
                if not isinstance(val, (str, int)):
                    raise TypeError(f'Invalid course\'s id in JSON: {val}')

    client = MoodleClient(url, key, endpoint, url_env_name, key_env_name)

    manager = SyncManager()

    client.fetch_courses(json_in=json_in_file, json_out=json_out)

    manager.update_jupyterhub(
                courses=client.courses if not json_out else None,
                json_path=json_out,
                in_file=in_file,
                out_file=out_file,
                **filters,
    )

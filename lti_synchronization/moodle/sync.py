import typing as t
from unittest import mock

from dotenv import load_dotenv

from .client.api import MoodleClient
from .integration.manager import SyncManager
from .typehints import PathLike, Filters


def synchronize(
    *,
    use_categories: bool = True,
    save_on_disk: bool = True,
    json_path: t.Optional[PathLike] = None,
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

    client = MoodleClient(url, key, endpoint, url_env_name, key_env_name)

    manager = SyncManager()

    if use_categories:

        client.use_categories()

    client.fetch_courses(
        json_path=json_path,
        save_on_disk=save_on_disk,
        **filters
    )

    default_configuration = open(SyncManager.path.in_file).read()

    new = mock.mock_open(read_data=default_configuration)

    with mock.patch('moodle.integration.template.open', new=new
    ) as mocked_open, mock.patch('moodle.integration.system.os.system', autospec=True
    ) as mocked_os, mock.patch('moodle.helper.Gradebook', autospec=True
    ) as mocked_gradebook:

        manager.update_jupyterhub(
                courses=client.courses if not save_on_disk else None,
                json_path=json_path,
                in_file=in_file,
                out_file=out_file,
                **filters,
            )

        print(mocked_os.call_args_list)

        print(mocked_open.call_args_list)

        print(mocked_gradebook.call_args_list)

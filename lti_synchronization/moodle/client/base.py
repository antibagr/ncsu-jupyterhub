import os
import typing as t

import requests
from requests.models import Response
from custom_inherit import DocInheritMeta
from loguru import logger

from moodle.response import FluidResponse
from moodle.typehints import JsonType
from moodle.utils import dump_json


class BaseAPIClient(metaclass=DocInheritMeta(style='google_with_merge', include_special_methods=True)):
    '''Moodle webservice interface.
    Based on gist of https://gist.github.com/kaqfa

    Initialize Moodle API Client.

    In order to make REST API requests a client need to obtain
    both Moodle URL and Moodle API token.

    Read more about Moodle REST API in docs/Setup Moodle.md

    You can pass url or token directly as a keyword-only
    string values or pass url_env_name or key_env_name keyword-only
    arguments to obtain url or token from environment if they
    differ from defaults.

    You can also provide client with a custom endpoint if it's
    neccesary in your case. With classic setup it defaults to
    /webservice/rest/server.php

    Args:
        url (:obj:`str`, optional): Moodle domain name. Defaults to None.
        key (:obj:`str`, optional): Moodle web service token. Defaults to None.
        endpoint (:obj:`str`, optional): Custom endpoint. Defaults to None.
        url_env_name (:obj:`str`, optional): Custom environment variable name. Defaults to None.
        key_env_name (:obj:`str`, optional): Custom environment variable name. Defaults to None.

    '''

    DEFAULT_ENDPOINT: str = '/webservice/rest/server.php'
    URL_ENV_NAME: str = 'MOODLE_API_URL'
    KEY_ENV_NAME: str = 'MOODLE_API_TOKEN'

    key: str
    url: str
    endpoint: str

    def __init__(
                self,
                url: t.Optional[str] = None,
                key: t.Optional[str] = None,
                endpoint: t.Optional[str] = None,
                url_env_name: t.Optional[str] = None,
                key_env_name: t.Optional[str] = None,
            ):

        # If url or key is not provided,
        # Check that appropriate enviroment variable is set
        # if env_name is provided prefer it over default one.
        # raise EnvironmentError if env is not set.
        for attr, env_name in (
            (url, 'url_env_name'),
            (key, 'key_env_name'),
        ):

            if attr is None:

                attr_name = locals()[env_name] or getattr(
                    self, env_name.upper())

                attr = os.getenv(attr_name)

                if not attr:

                    raise EnvironmentError(f'{attr_name} must be set.')

            setattr(self, env_name[:3], attr)

        self.endpoint: str = endpoint or self.DEFAULT_ENDPOINT

    def rest_api_parameters(
                self,
                in_args: t.Union[t.Sequence, t.Mapping],
                prefix: str = '',
                out_dict: t.Optional[dict] = None,
            ) -> JsonType:
        '''
        Transform dictionary/array structure to a flat dictionary, with key names
        defining the structure.

        Examples:

            Convert parameters::

                rest_api_parameters({'courses':[{'id': 1,'name': 'course1'}]})
                >>> {'courses[0][id]': 1, 'courses[0][name]':'course1'}
        '''

        if out_dict is None:
            out_dict = {}

        if not isinstance(in_args, (list, dict)):
            out_dict[prefix] = in_args
            return out_dict

        prefix += '{0}' if not prefix else '[{0}]'

        sequence = enumerate(in_args) if isinstance(
            in_args, list) else in_args.items()

        for idx, item in sequence:
            self.rest_api_parameters(item, prefix.format(idx), out_dict)

        return out_dict

    def call(self, api_func: str, **kwargs: t.Any) -> FluidResponse:
        '''
        Calls Moodle API <api_func> with keyword arguments.

        Args:
            api_func (:obj:`str`): name of function in Moodle web client.
            **kwargs: any parameters to send with the request.

        Examples:

            Calling *core_course_update_courses* function::

                call_mdl_function(
                    'core_course_update_courses',
                    courses = [{'id': 1, 'fullname': 'My favorite course'}]
                )

        Returns:
            FluidResponse: Convinient wrapper for received data.


        Raises:
            requests.HTTPError: Network or server error
            MoodleHTTPException: non successful HTTP status.
            MoodleAPIException: Syntax error in API call.
        '''

        parameters = self.rest_api_parameters(kwargs)

        logger.debug(f'''
        Calling {api_func!r}

        {dump_json(parameters)[1:-1] or 'Without parameters'}
        '''
                     )

        parameters.update({
                        'wstoken': self.key,
                        'moodlewsrestformat': 'json',
                        'wsfunction': api_func,
                       })

        resp: Response = requests.post(self.url + self.endpoint, parameters)

        resp.raise_for_status()

        # can raise MoodleHTTPException and MoodleAPIException
        return FluidResponse(resp, api_func)

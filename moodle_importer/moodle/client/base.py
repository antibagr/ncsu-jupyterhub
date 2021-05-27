import typing as t

import requests
from requests.models import Response
from loguru import logger

from moodle.response import FluidResponse
from moodle.typehints import JsonType
from moodle.utils import dump_json


class BaseAPIClient:
    '''
    Moodle webservice interface.
    Based on gist of https://gist.github.com/kaqfa
    '''

    DEFAULT_ENDPOINT: str = '/webservice/rest/server.php'

    key: str
    url: str
    endpoint: str

    def __init__(self, url: str, key: str, endpoint: t.Optional[str] = None):
        self.url = url
        self.key = key
        self.endpoint: str = endpoint or self.DEFAULT_ENDPOINT

    def rest_api_parameters(
                self,
                in_args: t.Union[t.Sequence, t.Dict],
                prefix: str = '',
                out_dict: t.Optional[t.Dict] = None,
            ) -> JsonType:
        '''
        Transform dictionary/array structure to a flat dictionary, with key names
        defining the structure.

        Example usage:

        >>> rest_api_parameters({'courses':[{'id': 1,'name': 'course1'}]})

        {
            'courses[0][id]': 1,
            'courses[0][name]':'course1'
        }

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

    def call(self, fname: str, **kwargs: t.Any) -> FluidResponse:
        '''
        Calls moodle API function with function name fname and keyword arguments.

        Example:
        >>> call_mdl_function('core_course_update_courses',
                               courses = [{'id': 1, 'fullname': 'My favorite course'}])

        Raises
            MoodleHTTPException: non successful HTTP status.
            MoodleAPIException: Syntax error in API call.
        '''

        # helpful while configuring mock
        # raise Exception('should not call on tests!')

        parameters = self.rest_api_parameters(kwargs)

        logger.debug(f'''
        Calling "{fname}"

        {dump_json(parameters)[1:-1] or 'Without parameters'}
        '''
                      )

        parameters.update({
                        'wstoken': self.key,
                        'moodlewsrestformat': 'json',
                        'wsfunction': fname,
                       })

        resp: Response = requests.post(self.url + self.endpoint, parameters)

        resp.raise_for_status()

        # can raise MoodleHTTPException and MoodleAPIException
        return FluidResponse(resp)
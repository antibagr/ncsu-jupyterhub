from requests.exceptions import HTTPError

from .utils import dump_json

from moodle.typehints import JsonType


class MoodleHTTPException(HTTPError):
    '''
    Non-success status code received after API Call.
    '''
    pass


class MoodleAPIException(ValueError):
    '''
    Exception raises when Moodle API responses with a dictionary
    containing "exception" key.
    '''

    def __init__(self, resp: JsonType):

        super().__init__(
            'Exception while calling Moodle API:'.center(39, '\n')
            + dump_json(resp)
        )

from .utils import dump_json

from moodle.typehints import JsonType


class MoodleAPIException(Exception):
    '''
    Exception raises when Moodle API responses with a dictionary
    containing "exception" key.
    '''

    def __init__(self, resp: JsonType):

        super().__init__(
            'Exception while calling Moodle API:'.center(39, '\n')
            + dump_json(resp)
        )

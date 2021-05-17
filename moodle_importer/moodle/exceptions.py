import typing as t

from .utils import dump_json


class MoodleAPIException(Exception):
    '''Documentation required.'''

    def __init__(self, resp: t.Dict):

        super().__init__(
            '\n\nException while calling Moodle API:\n\n'
            + dump_json(resp)
        )

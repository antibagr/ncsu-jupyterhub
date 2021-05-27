import typing as t

from requests.models import Response

from moodle.errors import MoodleHTTPException, MoodleAPIException
from moodle.utils import dump_json


class FluidResponse:
    '''
    Wrapper of a received HTTP response.
    Mimic received jsonify data.

    Args:
        resp (Response): HTTP Response from API

    Attributes:
        http_resp (type): Stored HTTP Response
        resp (JsonType): Json Data
    '''

    def __init__(self, resp: Response):

        if resp.status_code != 200:
            raise MoodleHTTPException(resp.status_code)

        self.http_resp = resp
        self.resp = self.http_resp.json()

        if isinstance(self.resp, dict) and 'exception' in self.resp:
            raise MoodleAPIException(self.resp)

    def __iter__(self) -> t.Generator[t.Any, None, None]:
        for el in self.resp:
            yield el

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return dump_json(self.resp)

    def print(self) -> None:
        '''
        Print shortcut for chaining commands.
        '''

        print(str(self))

    @property
    def __class__(self) -> str:
        return self.resp.__class__

    def __len__(self) -> int:
        return len(self.resp)

    def __getitem__(self, key: t.Union[str, int]) -> t.Any:
        return self.resp[key]

    def __setitem__(self, key: t.Union[str, int], value: t.Any) -> None:

        if not isinstance(self, dict):
            assert isinstance(key, int), f'index of a list must be integer. {type(key)} given.'

        self.resp[key] = value

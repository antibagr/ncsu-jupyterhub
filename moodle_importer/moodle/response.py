import typing as t

from requests.models import Response

from .utils import dump_json


class FluidResponse():
    '''Documentation required

    Args:
        resp (Response): HTTP Response from API

    Attributes:
        http_resp (type): Stored HTTP Response
        resp (JsonType): Json Data

    '''

    def __init__(self, resp: Response):
        self.http_resp = resp
        self.resp = self.http_resp.json()

    def __iter__(self) -> t.Generator[t.Any, None, None]:
        for el in self.resp:
            yield el

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return dump_json(self.resp)

    def print(self) -> None:
        '''
        Print shortcut for chaining style.
        '''

        print(self)

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

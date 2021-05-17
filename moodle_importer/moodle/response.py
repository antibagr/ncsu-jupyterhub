import typing as t

from requests.models import Response

from .utils import dump_json


class FluidResponse(dict):
    '''Documentation required

    Args:
        resp (Response): .

    Attributes:
        http_resp (type): .
        resp

    '''

    def __init__(self, resp: Response):
        self.http_resp = resp
        self.resp = self.http_resp.json()

    def __iter__(self) -> t.Generator[t.Any]:
        for el in self.resp:
            yield el

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return dump_json(self.resp)

    def print(self) -> None:
        print(self)

    @property
    def __class__(self) -> str:
        return self.resp.__class__

    def __len__(self) -> int:
        return len(self.resp)

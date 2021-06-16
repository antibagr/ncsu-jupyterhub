import typing as t

from moodle.helper import MoodleBasicHelper
from moodle.typehints import ByteParams, JsonType

from tornado.web import RequestHandler


class LTIHelper(MoodleBasicHelper):
    '''
    A class which contains various utility functions
    which work in conjunction with LTI requests.
    '''

    @staticmethod
    def get_client_protocol(handler: RequestHandler) -> t.Dict[str, str]:
        '''
        This is a copy of the jupyterhub-ltiauthenticator logic to get the first
        protocol value from the x-forwarded-proto list, assuming there is more than
        one value. Otherwise, this returns the value as-is.

        Extracted as a method to facilitate testing.

        Args:
          handler: a tornado.web.RequestHandler object

        Returns:
          A decoded dict with keys/values extracted from the request's arguments
        '''

        if 'x-forwarded-proto' in handler.request.headers:
            hops = (h.strip()
                    for h in handler.request.headers['x-forwarded-proto'].split(','))
            protocol = next(hops)
        else:
            protocol = handler.request.protocol

        return protocol

    @staticmethod
    def convert_request_to_dict(arguments: ByteParams) -> JsonType:
        '''
        Converts the arguments obtained from a request to a dict.

        Args:
          arguments: Raw arguments from an authenticator.

        Returns:
          A decoded dict with keys/values extracted from the request's arguments
        '''

        return dict((k, v[0].decode()) for k, v in arguments.items())

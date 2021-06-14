import json
import os
import secrets
import time
import typing as t
import uuid
from asyncio import AbstractEventLoop
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest
from Crypto.PublicKey import RSA
from moodle.authentication.helper import LTIHelper
from moodle.lti13.handlers import LTI13ConfigHandler, LTI13JWKSHandler
from moodle.typehints import JsonType, ByteParams
from moodle.utils import dump_json
from nbgrader.api import Course
from oauthlib.oauth1.rfc5849 import signature
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from tornado.httputil import HTTPHeaders, HTTPServerRequest
from tornado.web import Application, RequestHandler


def create_params(**in_dict: JsonType) -> ByteParams:
    '''
        {'f': 'foo', 'b': 'bar'} => {'f': [b'foo'], 'b': [b'bar']}
    '''

    return {k: [bytes(v, encoding='utf-8')] for k, v in in_dict.items()}


@pytest.fixture
def test_dir() -> Path:
    return Path(__file__).resolve().parent


@pytest.fixture
def pem_file(tmp_path) -> str:
    '''
    Create a test private key file used with LTI 1.3 request/reponse flows
    '''

    key = RSA.generate(2048)

    key_path = f'{tmp_path}/private.key'

    with open(key_path, 'wb') as content_file:
        content_file.write(key.exportKey('PEM'))

    return key_path


@pytest.fixture
def lti13_config_environ(pem_file) -> t.Generator[None, None, None]:
    '''
    Set the enviroment variables used in Course class
    '''

    with patch.dict(os.environ, {
        'LTI13_PRIVATE_KEY': pem_file,
        'LTI13_TOKEN_URL': 'https://my.platform.domain/login/oauth2/token',
        'LTI13_ENDPOINT': 'https://my.platform.domain/api/lti/security/jwks',
        'LTI13_CLIENT_ID': 'https://my.platform.domain/login/oauth2/token',
        'LTI13_AUTHORIZE_URL': 'https://my.platform.domain/api/lti/authorize_redirect',
    }):
        yield


@pytest.fixture
def make_http_response() -> HTTPResponse:
    async def _make_http_response(
        handler: RequestHandler,
        code: int = 200,
        reason: str = 'OK',
        headers: t.Optional[HTTPHeaders] = None,
        effective_url: str = 'http://hub.example.com/',
        body: t.Optional[JsonType] = None,
    ) -> HTTPResponse:
        '''
        Creates an HTTPResponse object from a given request. The buffer key is used to
        add data to the response's body using an io.StringIO object. This factory method assumes
        the body's buffer is an encoded JSON string.
        This awaitable factory method requires a tornado.web.RequestHandler object with a valid
        request property, which in turn requires a valid jupyterhub.auth.Authenticator object. Use
        a dictionary to represent the StringIO body in the response.
        Example:
            response_args = {'handler': local_handler.request, 'body': {'code': 200}}
            http_response = await factory_http_response(**response_args)
        Args:
        handler: tornado.web.RequestHandler object.
        code: response code, e.g. 200 or 404
        reason: reason phrase describing the status code
        headers: HTTPHeaders (response header object), use the dict within the constructor, e.g.
            {'content-type': 'application/json'}
        effective_url: final location of the resource after following any redirects
        body: dictionary that represents the StringIO (buffer) body
        Returns:
        A tornado.client.HTTPResponse object
        '''

        dict_to_buffer = StringIO(json.dumps(
            body or {'foo': 'bar'})) if body is not None else None

        return HTTPResponse(
            request=handler,
            code=code,
            reason=reason,
            headers=headers or HTTPHeaders(
                {'content-type': 'application/json'}),
            effective_url=effective_url,
            buffer=dict_to_buffer,
        )

    return _make_http_response


@pytest.fixture
def make_mock_request_handler() -> t.Callable[[RequestHandler, str, str, t.Any], RequestHandler]:
    '''
    Sourced from https://github.com/jupyterhub/oauthenticator/blob/master/oauthenticator/tests/mocks.py
    '''

    def _make_mock_request_handler(
        handler: RequestHandler,
        uri: str = 'https://hub.example.com',
        method: str = 'GET',
        **settings: dict,
    ) -> RequestHandler:
        '''Instantiate a Handler in a mock application'''

        application = Application(
            hub=Mock(base_url='/hub/', server=Mock(base_url='/hub/')),
            cookie_secret=os.urandom(32),
            db=Mock(rollback=Mock(return_value=None)),
            **settings,
        )

        request = HTTPServerRequest(method=method, uri=uri, connection=Mock())

        handler = RequestHandler(application=application, request=request)

        handler._transforms = []

        return handler

    return _make_mock_request_handler


@pytest.fixture
def mock_tornado_client(
    request, make_http_response, make_mock_request_handler
) -> t.Generator[AsyncHTTPClient, None, None]:
    '''
    Creates a patch of AsyncHttpClient.fetch method, useful when other tests are making http request
    '''
    local_handler = make_mock_request_handler(RequestHandler)

    test_request_body_param = (
        request.param if hasattr(request, 'param') else {'message': 'ok'}
    )

    with patch.object(
        AsyncHTTPClient,
        'fetch',
        return_value=make_http_response(
            handler=local_handler.request,
            body=test_request_body_param
        ),
    ):
        yield AsyncHTTPClient()


@pytest.fixture
def config_handler(
            lti13_config_environ: None,
            make_mock_request_handler: RequestHandler
        ) -> LTI13ConfigHandler:

    hdl = make_mock_request_handler(RequestHandler)

    return LTI13ConfigHandler(hdl.application, hdl.request)


@pytest.fixture
def jwks_handler(
            lti13_config_environ: None,
            make_mock_request_handler: RequestHandler
        ) -> LTI13JWKSHandler:

    hdl = make_mock_request_handler(RequestHandler)

    return LTI13JWKSHandler(hdl.application, hdl.request)


@pytest.fixture
@patch('tornado.web.RequestHandler.write')
def mock_write(
            mock_write: MagicMock,
            event_loop: AbstractEventLoop,
            config_handler: LTI13ConfigHandler
        ) -> MagicMock:

    # this method writes the output to internal buffer
    event_loop.run_until_complete(config_handler.get())

    return mock_write


@pytest.fixture
def json_arg(mock_write: MagicMock) -> dict:

    # call_args is a list
    # so we're only extracting the json arg

    return json.loads(mock_write.call_args[0][0])


@pytest.fixture
def jws(test_dir: Path) -> JsonType:
    '''
    Returns valid json after decoding JSON Web Token (JWT) for resource link launch (core).
    '''

    with open(test_dir / 'data' / 'lti_resource_link.json', 'r') as f:

        jws = json.loads(f.read())

    return jws


@pytest.fixture
def jws_with_privacy(test_dir: Path) -> JsonType:
    '''
    Returns valid json after decoding JSON Web Token (JWT) for resource link launch (core)
    when Privacy is enabled.
    '''

    with open(test_dir / 'data' / 'lti_resource_link_with_privacy.json', 'r') as f:

        jws = json.loads(f.read())

    return jws


@pytest.fixture
def get_jwt_id_token() -> t.Callable:

    def _make_lti13_jwt_id_token(json_lti13_launch_request: JsonType):
        '''
        Returns a valid jwt lti13 id token from a json
        We can use the `jws`
        or `jws_with_privacy`
        fixture to create the json then call this method.
        '''

        encoded_jwt = jwt.encode(
            json_lti13_launch_request, 'secret', algorithm='HS256')

        return encoded_jwt

    return _make_lti13_jwt_id_token


@pytest.fixture
def lti13_login_params() -> ByteParams:
    '''
    Creates a dictionary with k/v's that emulates an initial login request.
    '''

    return create_params(
        client_id='125900000000000085',
        iss='https://platform.vendor.com',
        login_hint='185d6c59731a553009ca9b59ca3a885104ecb4ad',
        target_link_uri='https://edu.example.com/hub',
        lti_message_hint='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ2ZXJpZmllciI6IjFlMjk2NjEyYjZmMjdjYmJkZTg5YmZjNGQ1ZmQ5ZDBhMzhkOTcwYzlhYzc0NDgwYzdlNTVkYzk3MTQyMzgwYjQxNGNiZjMwYzM5Nzk1Y2FmYTliOWYyYTgzNzJjNzg3MzAzNzAxZDgxMzQzZmRmMmIwZDk5ZTc3MWY5Y2JlYWM5IiwiY2FudmFzX2RvbWFpbiI6ImlsbHVtaWRlc2suaW5zdHJ1Y3R1cmUuY29tIiwiY29udGV4dF90eXBlIjoiQ291cnNlIiwiY29udGV4dF9pZCI6MTI1OTAwMDAwMDAwMDAwMTM2LCJleHAiOjE1OTE4MzMyNTh9.uYHinkiAT5H6EkZW9D7HJ1efoCmRpy3Id-gojZHlUaA',
    )


@pytest.fixture
def lti13_auth_params():
    '''
    Creates a dictionary with k/v's that emulates a login request.
    '''

    return create_params(
        response_type='id_token',
        scope='openid',
        response_mode='form_post',
        prompt='none',
        client_id = '125900000000000081',
        redirect_uri = 'https://acme.moodle.com/hub/oauth_callback',
        lti_message_hint = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ2ZXJpZmllciI6IjFlMjk2NjEyYjZmMjdjYmJkZTg5YmZjNGQ1ZmQ5ZDBhMzhkOTcwYzlhYzc0NDgwYzdlNTVkYzk3MTQyMzgwYjQxNGNiZjMwYzM5Nzk1Y2FmYTliOWYyYTgzNzJjNzg3MzAzNzAxZDgxMzQzZmRmMmIwZDk5ZTc3MWY5Y2JlYWM5IiwiY2FudmFzX2RvbWFpbiI6ImlsbHVtaWRlc2suaW5zdHJ1Y3R1cmUuY29tIiwiY29udGV4dF90eXBlIjoiQ291cnNlIiwiY29udGV4dF9pZCI6MTI1OTAwMDAwMDAwMDAwMTM2LCJleHAiOjE1OTE4MzMyNTh9.uYHinkiAT5H6EkZW9D7HJ1efoCmRpy3Id-gojZHlUaA',
        login_hint = '185d6c59731a553009ca9b59ca3a885104ecb4ad',
        state = 'eyJzdGF0ZV9pZCI6ICI2ZjBlYzE1NjlhM2E0MDJkYWM2MTYyNjM2MWQwYzEyNSIsICJuZXh0X3VybCI6ICIvIn0=',
        nonce = '38048502278109788461591832959',
    )


@pytest.fixture
def lti13_login_params_dict(lti13_login_params: ByteParams) -> JsonType:
    '''
    Return the initial LTI 1.3 authorization request as a dict
    '''

    return LTIHelper.convert_request_to_dict(lti13_login_params)


@pytest.fixture(scope='function')
def lti13_auth_params_dict(lti13_auth_params: ByteParams) -> JsonType:
    '''
    Return the initial LTI 1.3 authorization request as a dict
    '''

    return LTIHelper.convert_request_to_dict(lti13_auth_params)


@pytest.fixture
def make_auth_state_dict() -> JsonType:
    '''
    Creates an authentication dictionary
    with default name and auth_state k/v's
    '''

    def _make_auth_state_dict(
        username: str = 'foo',
        assignment_name: str = 'myassignment',
        course_id: str = 'intro101',
        lms_user_id: str = 'abc123',
        user_role: str = 'Learner',
    ):
        return {
            'name': username,
            'auth_state': {
                'assignment_name': assignment_name,
                'course_id': course_id,
                'lms_user_id': lms_user_id,
                'user_role': user_role,
            },  # noqa: E231
        }

    return _make_auth_state_dict

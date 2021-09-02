import hashlib
import typing as t
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from oauthenticator.oauth2 import _deserialize_state
from oauthenticator.oauth2 import _serialize_state
from tornado.web import RequestHandler

from tests.typehints import MonkeyPatch
from moodle.typehints import ByteParams, JsonType
from moodle.authentication.authenticator import LTI13LaunchValidator
from moodle.authentication.handlers import LTI13LoginHandler
from moodle.authentication.helper import LTIHelper


@pytest.fixture
def local_handler(make_mock_request_handler: RequestHandler) -> LTI13LoginHandler:
    return make_mock_request_handler(LTI13LoginHandler)


@pytest.mark.asyncio
async def test_login_handler_raises_env_error(
    monkeypatch: MonkeyPatch,
    lti13_login_params_dict: JsonType,
    local_handler: LTI13LoginHandler,
):
    '''
    Does the LTI13LoginHandler raise a missing argument
    error if request body doesn't have any arguments?
    '''

    monkeypatch.setenv('LTI13_AUTHORIZE_URL', '')

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=lti13_login_params_dict):

        with pytest.raises(EnvironmentError):
            LTI13LoginHandler(local_handler.application,
                              local_handler.request).post()


@pytest.mark.asyncio
async def test_login_handler_invokes_convert_request_to_dict_method(
    lti13_login_params_dict: JsonType,
    local_handler: LTI13LoginHandler,
):
    '''
    Does the LTI13LoginHandler call the LTIHelper convert_request_to_dict
    function once it receiving the post request?
    '''

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=lti13_login_params_dict) as mock_convert:
        with patch.object(LTI13LoginHandler, 'authorize_redirect', return_value=None):

            LTI13LoginHandler(local_handler.application,
                              local_handler.request).post()

            assert mock_convert.called


@pytest.mark.asyncio
@patch.object(LTI13LoginHandler, 'authorize_redirect', return_value=None)
async def test_lti_13_login_handler_invokes_validate_login_request_method(
    mocked_redirect: MagicMock,
    lti13_auth_params_dict: JsonType,
    local_handler: LTI13LoginHandler,
):
    '''
    Does the LTI13LoginHandler call the LTI13LaunchValidator
    validate_login_request function once it receiving the post request?
    '''

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=lti13_auth_params_dict):
        with patch.object(
            LTI13LaunchValidator,
            'validate_login_request',
            return_value=True
        ) as mock_validate:

            LTI13LoginHandler(local_handler.application,
                              local_handler.request).post()

            assert mock_validate.called


@pytest.mark.asyncio
@patch.object(LTI13LaunchValidator, 'validate_login_request', return_value=True)
async def test_lti_13_login_handler_invokes_redirect_method(
    mocked_login: MagicMock,
    local_handler: LTI13LoginHandler,
    lti13_auth_params_dict: JsonType,
):
    '''
    Does the LTI13LoginHandler call the redirect function once it
    receiving the post request?
    '''

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=lti13_auth_params_dict):
        with patch.object(LTI13LoginHandler, 'authorize_redirect', return_value=None) as mock_redirect:

            LTI13LoginHandler(local_handler.application,
                              local_handler.request).post()

            assert mock_redirect.called


@pytest.mark.asyncio
async def test_login_redirect_values(
    local_handler: LTI13LoginHandler,
    lti13_auth_params_dict: JsonType,
):
    '''
    Does the LTI13LoginHandler correctly set all variables needed for the redict method
    after receiving it from the validator?
    '''

    expected = lti13_auth_params_dict

    state_id = uuid4().hex

    expected_state = _serialize_state({'state_id': state_id, 'next_url': ''})

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=lti13_auth_params_dict):
        with patch.object(LTI13LaunchValidator, 'validate_login_request', return_value=True):
            with patch.object(LTI13LoginHandler, 'get_state', return_value=expected_state):
                with patch.object(LTI13LoginHandler, 'authorize_redirect', return_value=None) as mock_auth_redirect:

                    nonce_raw = hashlib.sha256(expected_state.encode())

                    expected_nonce = nonce_raw.hexdigest()

                    LTI13LoginHandler(local_handler.application,
                                      local_handler.request).post()

                    mock_auth_redirect.assert_called_once_with(
                        client_id=expected['client_id'],
                        login_hint=expected['login_hint'],
                        lti_message_hint=expected['lti_message_hint'],
                        redirect_uri='https://127.0.0.1/hub/oauth_callback',
                        state=expected_state,
                        nonce=expected_nonce,
                    )


@pytest.mark.skip
@pytest.mark.asyncio
async def test_lti_13_login_handler_sets_state_with_next_url_obtained_from_target_link_uri(
    local_handler: LTI13LoginHandler,
    lti13_login_params: ByteParams,
):
    '''
    Do we get the expected nonce value result after hashing
    the state and returning the hexdigest?
    '''

    lti13_login_params['target_link_uri'] = [
        lti13_login_params['target_link_uri'][0] + b'?next=/user-redirect/lab']

    decoded_dict = LTIHelper.convert_request_to_dict(lti13_login_params)

    with patch.object(LTIHelper, 'convert_request_to_dict', return_value=decoded_dict):
        with patch.object(LTI13LaunchValidator, 'validate_login_request', return_value=True):
            with patch.object(LTI13LoginHandler, 'authorize_redirect', return_value=None):

                expected_state_json = {
                    'state_id': '6f0ec1569a3a402dac61626361d0c125',
                    'next_url': '/user-redirect/lab',
                }

                login_instance = LTI13LoginHandler(
                    local_handler.application, local_handler.request)

                login_instance.post()

                assert login_instance._state is not None

                state_decoded = _deserialize_state(login_instance._state)

                print(state_decoded)

                assert state_decoded['next_url'] == expected_state_json['next_url']

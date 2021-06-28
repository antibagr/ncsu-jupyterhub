import typing as t
from unittest.mock import patch

import pytest
from tornado.web import HTTPError
from tornado.httpclient import AsyncHTTPClient

from moodle.authentication.validator import LTI13LaunchValidator
from moodle.typehints import JsonType


@pytest.fixture
def validator() -> LTI13LaunchValidator:
    return LTI13LaunchValidator()


@pytest.mark.skip
@pytest.mark.asyncio
async def test_validator_jwt_verify_and_decode_invokes_retrieve_matching_jwk(
    jws: JsonType,
    get_jwt_id_token: t.Callable,
    validator: LTI13LaunchValidator,
    client: AsyncHTTPClient,
):
    '''
    Does the validator jwt_verify_and_decode method invoke the retrieve_matching_jwk method?
    '''

    jwks_endoint = 'https://my.platform.domain/api/lti/security/jwks'

    with patch.object(validator, '_retrieve_matching_jwk', return_value=None) as mock_retrieve_matching_jwks:

        await validator.jwt_verify_and_decode(
            get_jwt_id_token(jws),
            jwks_endoint,
            verify=True,
        )

        assert mock_retrieve_matching_jwks.called


@pytest.mark.asyncio
async def test_jwt_verify_raises_an_error_with_no_retrieved_platform_keys(
    jws: JsonType,
    get_jwt_id_token: t.Callable,
    validator: LTI13LaunchValidator,
    mock_tornado_client: AsyncHTTPClient,
):
    '''
    Does the validator jwt_verify_and_decode method return None
    when no keys are returned from the retrieve_matching_jwk method?
    '''

    jwks_endoint = 'https://my.platform.domain/api/lti/security/jwks'

    with (pytest.raises(ValueError)):
        await validator.jwt_verify_and_decode(
            get_jwt_id_token(jws),
            jwks_endoint,
            verify=True,
        )


@pytest.mark.parametrize('field, value, passes', [
    ('message_type', 'FakeLinkRequest', False),
    ('version', '1.0.0', False),
    ('resource_link/id', '', False),
    ('context/label', '', False),
    ('message_type', 'LtiDeepLinkingRequest', True),
    ('deployment_id', '', True),
    ('target_link_uri', '', True),
    ('roles', '', True),
])
def test_validator_with_missed_fields(
    validator: LTI13LaunchValidator,
    jws: JsonType,
    field: str, value: str, passes: bool,
):
    '''
    Is the JWT valid with an incorrect claim?
    '''

    base = 'https://purl.imsglobal.org/spec/lti/claim/'

    if '/' in field:

        field, key = field.split('/')

        jws[base + field][key] = value

    else:

        jws[base + field] = value

    if passes:

        assert validator.validate_launch_request(jws) is True

    else:

        with pytest.raises(HTTPError):
            validator.validate_launch_request(jws)


def test_jwt_with_missed_claims(validator: LTI13LaunchValidator):
    '''
    Is the JWT valid with an incorrect message type claim?
    '''

    with pytest.raises(HTTPError):
        validator.validate_login_request({'key1': 'value1'})


def test_validate_with_required_params_in_initial_auth_request(
            validator: LTI13LaunchValidator,
            lti13_login_params: t.Dict[str, t.List[bytes]],
        ):
    '''
    Is the JWT valid with an correct message type claim?
    '''

    assert validator.validate_login_request(lti13_login_params) is True


def test_validate_with_privacy_enabled(validator: LTI13LaunchValidator, jws_with_privacy: JsonType):
    '''
    Is the JWT valid when privacy is enabled?
    '''

    assert validator.validate_launch_request(jws_with_privacy)


def test_validate_resource_ling_is_not_required_for_deep_linking_request(
    validator: LTI13LaunchValidator,
    jws: JsonType,
):
    '''
    Is the JWT valid with for LtiDeepLinkingRequest?
    '''

    base = 'https://purl.imsglobal.org/spec/lti/claim/'

    jws[base + 'message_type'] = 'LtiDeepLinkingRequest'

    jws.pop(base + 'resource_link')

    assert validator.validate_launch_request(jws)

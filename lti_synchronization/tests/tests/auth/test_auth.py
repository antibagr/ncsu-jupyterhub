import typing

from unittest import mock
from unittest.mock import patch, MagicMock

import pytest
from tornado.web import RequestHandler

from moodle.authentication.authenticator import LTI13Authenticator
from moodle.authentication.authenticator import LTIHelper
from moodle.authentication.validator import LTI13LaunchValidator


CLAIM = 'https://purl.imsglobal.org/spec/lti/claim/'
PERSON = 'http://purl.imsglobal.org/vocab/lis/v2/institution/person#'


@pytest.fixture
def mock_nbhelper():
    return MagicMock()


@pytest.fixture
def mock_validation() -> mock.Mock:
    with patch.object(
        LTI13LaunchValidator, 'validate_launch_request', return_value=True
    ) as mocked:
        yield mocked


def patch_handler(
        value: typing.Any,
        **kwargs: typing.Any,
) -> mock.Mock:
    return patch.object(
        RequestHandler,
        'get_argument',
        return_value=value,
        **kwargs,
    )


@pytest.fixture
def request_handler(
        make_mock_request_handler: typing.Callable,
) -> RequestHandler:
    authenticator = LTI13Authenticator()
    handler = make_mock_request_handler(
        RequestHandler,
        authenticator=authenticator,
    )
    handler.auth = authenticator
    return handler


@pytest.mark.asyncio
async def test_authenticator_invokes_lti13validator_handler_get_argument(
    get_jwt_id_token,
    jws,

    mock_nbhelper,
    request_handler: RequestHandler,
):
    '''
    Does the authenticator invoke the RequestHandler get_argument method?
    '''
    with patch_handler(
        value=get_jwt_id_token(jws)
    ) as mocked_get_arg:
        await request_handler.auth.authenticate(request_handler)
        assert mocked_get_arg.called


@pytest.mark.asyncio
async def test_authenticator_invokes_lti13validator_jwt_verify_and_decode(
        jws,

        mock_nbhelper,
        request_handler: RequestHandler,
):
    '''
    Does the authenticator invoke the LTI13Validator
    jwt_verify_and_decode method?
    '''
    with patch_handler(value=None), patch.object(
        LTI13LaunchValidator,
        'jwt_verify_and_decode',
        return_value=jws,
    ) as mock_verify_and_decode:
        await request_handler.auth.authenticate(request_handler)
        assert mock_verify_and_decode.called


@pytest.mark.asyncio
async def test_authenticator_invokes_lti13validator_validate_launch_request(
        jws,
        get_jwt_id_token,

        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Does the request_handler.auth invoke the LTI13Validator
    validate_launch_request method?
    '''
    with patch_handler(value=get_jwt_id_token(jws)):
        await request_handler.auth.authenticate(request_handler)
        assert mock_validation.called


@pytest.mark.asyncio
async def test_authenticator_invokes_lti_helper_format_string(
        jws,
        get_jwt_id_token,

        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Does the request_handler.auth invoke the LTIHelper format_string method?
    '''
    with patch_handler(value=get_jwt_id_token(jws)):
        with patch.object(
            LTIHelper, 'format_string', return_value=True
        ) as mocked:
            await request_handler.auth.authenticate(request_handler)
            assert mocked.called


@pytest.mark.asyncio
async def test_auth_returns_course_id_in_auth_state_with_valid_resource_link_request(
        make_auth_state_dict,
        jws,
        get_jwt_id_token,

        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid course_id when receiving a valid resource link request?
    '''
    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['course_id'] == 'intro101'


@pytest.mark.asyncio
async def test_auth_returns_auth_state_with_course_id_normalized(
        make_auth_state_dict,
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid course_id when receiving a valid resource link request?
    '''
    # change the context label to uppercase
    link_request = jws
    link_request[CLAIM + 'context']['label'] = 'CourseID-WITH_LARGE NAME'
    with patch_handler(value=get_jwt_id_token(link_request)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['course_id'] == 'courseid-with_large_name'


# @pytest.mark.skip(reason='No need to work with email name')
@pytest.mark.asyncio
async def test_auth_returns_auth_state_name_from_lti13_email_claim(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when only including an email
    to the resource link request?
    '''
    lti13_json = jws
    lti13_json['name'] = ''
    lti13_json['given_name'] = ''
    lti13_json['family_name'] = ''
    lti13_json['email'] = 'usertest@example.com'
    with patch_handler(value=get_jwt_id_token(lti13_json)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == 'usertest'


# @pytest.mark.skip(reason='No need to work with username in Moodle.')
@pytest.mark.asyncio
async def test_auth_returns_username_in_auth_state_with_with_name(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when only including the name
    in the resource link request?
    '''
    jws['name'] = 'Foo'
    jws['given_name'] = ''
    jws['family_name'] = ''
    jws['email'] = ''
    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == 'foo'


# @pytest.mark.skip(reason='No need to work with given name in Moodle.')
@pytest.mark.asyncio
async def test_auth_returns_username_in_auth_state_with_with_given_name(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when only including the
    given name in the resource link request?
    '''
    jws['name'] = ''
    jws['given_name'] = 'Foo Bar'
    jws['family_name'] = ''
    jws['email'] = ''
    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == 'foo_bar'


# @pytest.mark.skip(reason='No need to work with family name')
@pytest.mark.asyncio
async def test_auth_returns_username_in_auth_state_with_family_name(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when only including the family
    name in the resource link request?
    '''
    jws['name'] = ''
    jws['given_name'] = ''
    jws['family_name'] = 'Family name'
    jws['email'] = ''
    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == 'family_name'


@pytest.mark.asyncio
async def test_auth_returns_username_in_auth_state_with_person_sourcedid(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when only including lis
    person sourcedid resource link request?
    '''
    jws['name'] = ''
    jws['given_name'] = ''
    jws['family_name'] = ''
    jws['email'] = ''
    jws[CLAIM + 'lis']['person_sourcedid'] = 'abc123'

    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == 'abc123'


@pytest.mark.asyncio
async def test_auth_returns_username_in_auth_state_with_privacy_enabled(
        jws_with_privacy,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we get a valid username when initiating the
    login flow with privacy enabled?
    '''
    with patch_handler(
        value=get_jwt_id_token(jws_with_privacy)
    ):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['name'] == '4'


@pytest.mark.asyncio
async def test_auth_returns_learner_role_in_auth_state(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we set the learner role in the auth_state when receiving
    a valid resource link request?
    '''
    jws[CLAIM + 'roles'] = PERSON + 'Learner'

    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['user_role'] == 'Learner'


@pytest.mark.asyncio
async def test_auth_returns_instructor_role_in_auth_state_with_instructor_role(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we set the instructor role in the auth_state when
    receiving a valid resource link request?
    '''
    jws[CLAIM + 'roles'] = [PERSON + 'Instructor']

    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['user_role'] == 'Instructor'


@pytest.mark.asyncio
async def test_auth_returns_student_role_in_auth_state_with_learner_role(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we set the student role in the auth_state when receiving
    a valid resource link request with the Learner role?
    '''
    # set our role to test
    jws[CLAIM + 'roles'] = [PERSON + 'Learner']
    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['user_role'] == 'Learner'


@pytest.mark.asyncio
async def test_auth_returns_student_role_in_auth_state_with_student_role(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we set the student role in the auth_state when receiving
    a valid resource link request with the Student role?
    '''
    # set our role to test
    jws[CLAIM + 'roles'] = [PERSON + 'Student']

    with patch_handler(value=get_jwt_id_token(jws)):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['user_role'] == 'Learner'


@pytest.mark.asyncio
async def test_auth_returns_learner_role_in_auth_state_with_empty_roles(
        jws,
        get_jwt_id_token,
        mock_nbhelper,
        request_handler: RequestHandler,
        mock_validation: mock.Mock,
):
    '''
    Do we set the learner role in the auth_state when receiving
    resource link request with empty roles?
    '''
    jws[CLAIM + 'roles'] = []

    with patch_handler(
        value=get_jwt_id_token(jws)
    ):
        result = await request_handler.auth.authenticate(request_handler)
        assert result['auth_state']['user_role'] == 'Learner'

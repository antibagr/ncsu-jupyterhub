from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
from tornado.web import RequestHandler

from moodle.authentication.authenticator import LTI13Authenticator
from moodle.grades.handlers import SendGradesHandler


@pytest.fixture
def mock_tornado_write() -> MagicMock:
    with patch('tornado.web.RequestHandler.write') as mocker:
        yield mocker


@pytest.fixture()
def grades_client(make_mock_request_handler: RequestHandler) -> SendGradesHandler:
    '''
    Mock neccessary attributes.

    Returns:
        SendGradesHandler: Client to send grades

    '''

    def mock_user() -> Mock:
        mock_user = Mock()
        attrs = {
            'get_auth_state.side_effect': AsyncMock(return_value=list()),
        }
        mock_user.configure_mock(**attrs)
        return mock_user

    request_handler = make_mock_request_handler(
        RequestHandler, authenticator=LTI13Authenticator,
    )

    send_grades_handler = SendGradesHandler(
        request_handler.application, request_handler.request
    )

    send_grades_handler._jupyterhub_user = mock_user()

    return send_grades_handler


@pytest.mark.asyncio
async def test_SendGrades_calls_GradeSender(
    mock_tornado_write: MagicMock,
    grades_client: SendGradesHandler
):
    '''
    Does the SendGradesHandler uses authenticator_class
    property to get what authenticator was set?
    '''

    with patch('moodle.grades.handlers.LTI13GradeSender') as mock_sender:

        mock_sender.return_value.send_grades = AsyncMock()

        await grades_client.post('course_example', 'assignment_test')

        assert mock_sender.called


@pytest.mark.asyncio
async def test_SendGradesHandler_gets_authenticator_from_settings(
    mock_tornado_write: MagicMock,
    grades_client: SendGradesHandler
):
    '''
    Does the SendGradesHandler.authenticator_class
    property gets its value from jhub settings?
    '''

    assert grades_client.authenticator is LTI13Authenticator


@pytest.mark.asyncio
async def test_SendGradesHandler_calls_write_method(
    mock_tornado_write: MagicMock,
    grades_client: SendGradesHandler
):
    '''
    Does the SendGradesHandler call write base method?
    '''

    with patch('moodle.grades.handlers.LTI13GradeSender') as mock_sender:

        mock_sender.return_value.send_grades = AsyncMock()

        await grades_client.post('course_example', 'assignment_test')

        assert mock_tornado_write.called

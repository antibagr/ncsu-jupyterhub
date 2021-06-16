import os
from unittest.mock import patch, Mock, AsyncMock

import pytest
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from tornado.httputil import HTTPHeaders
from tornado.web import RequestHandler

from moodle.errors import AssignmentWithoutGradesError, GradesSenderMissingInfoError
from moodle.grades.senders import LTI13GradeSender


def test_sender_get_course(lti13_config_environ: None):

    with patch('moodle.helper.Gradebook', autospec=True) as mocked_gradebook:

        LTI13GradeSender('foo_course', 'bar_assignment')

        mocked_gradebook.assert_called_once_with(
            'sqlite:////home/grader-foo_course/grader.db',
            course_id='foo_course',
        )


@pytest.mark.asyncio
async def test_sender_exception_with_no_grades(
    lti13_config_environ: None,
    mock_nbgrader_helper: Mock
):

    sender = LTI13GradeSender('course-id', 'lab')

    with patch.object(sender, '_retrieve_grades_from_db', return_value=(0, [])):
        with pytest.raises(AssignmentWithoutGradesError):
            await sender.send_grades()


@pytest.mark.asyncio
async def test_sender_calls_set_access_token_header_before_to_send_grades(
    lti13_config_environ: None,
    make_http_response: HTTPResponse,
    make_mock_request_handler: RequestHandler,
    mock_nbgrader_helper: Mock,
):

    sender = LTI13GradeSender('course-id', 'lab')

    local_handler = make_mock_request_handler(RequestHandler)

    tok_result = {'token_type': '', 'access_token': ''}

    grades = (10, [{'score': 10, 'lms_user_id': 'id'}])

    line_item_result = {'label': 'lab', 'id': 'line_item_url', 'scoreMaximum': 40}

    resp = [
        make_http_response(
            handler=local_handler.request, body=[line_item_result]
        ),
        make_http_response(
            handler=local_handler.request, body=line_item_result
        ),
        make_http_response(handler=local_handler.request, body=[]),
    ]

    with patch('moodle.grades.senders.get_lms_access_token', return_value=tok_result) as mock_get_token:

        with patch.object(sender, '_retrieve_grades_from_db', return_value=grades):

            with patch.object(AsyncHTTPClient, 'fetch', side_effect=resp):

                await sender.send_grades()

                mock_get_token.assert_called_once_with(
                    os.getenv('LTI13_TOKEN_URL'),
                    os.getenv('LTI13_PRIVATE_KEY'),
                    os.getenv('LTI13_TOKEN_URL'),
                )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mock_tornado_client', [[]], indirect=True
)
async def test_sender_exception_without_line_items(
    lti13_config_environ: None,
    mock_nbgrader_helper: Mock,
    mock_tornado_client: AsyncHTTPClient,
):

    sender = LTI13GradeSender('course-id', 'lab')

    tok_result = {'token_type': '', 'access_token': ''}

    with patch('moodle.grades.senders.get_lms_access_token', return_value=tok_result):

        with patch.object(sender, '_retrieve_grades_from_db', return_value=(lambda: 10, [{'score': 10}])):

            with pytest.raises(GradesSenderMissingInfoError):
                await sender.send_grades()


@pytest.mark.asyncio
async def test_get_lineitems_from_url_method_does_fetch_lineitems_from_url(
    lti13_config_environ: None,
    mock_nbgrader_helper: Mock,
    make_http_response: HTTPResponse,
    make_mock_request_handler: RequestHandler,
):

    local_handler = make_mock_request_handler(RequestHandler)

    resp = make_http_response(handler=local_handler.request)

    sender = LTI13GradeSender('course-id', 'lab')

    lineitems_url = 'https://example.moodle.com/api/lti/courses/111/line_items'

    with patch.object(AsyncHTTPClient, 'fetch', return_value=resp) as mock_client:

        await sender._get_lineitems_from_url(lineitems_url)

        mock_client.assert_called_with(lineitems_url, method='GET', headers={})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mock_tornado_client',
    [[{
        'id': 'value',
        'scoreMaximum': 0.0,
        'label': 'label',
        'resourceLinkId': 'abc',
    }]],
    indirect=True,
)
async def test_get_lineitems_from_url_method_sets_all_lineitems_property(
    lti13_config_environ: None,
    mock_nbgrader_helper: Mock,
    mock_tornado_client: AsyncHTTPClient,
):

    sender = LTI13GradeSender('course-id', 'lab')

    await sender._get_lineitems_from_url('https://example.moodle.com/api/lti/courses/111/line_items')

    assert len(sender.all_lineitems) == 1


@pytest.mark.asyncio
async def test_get_lineitems_from_url_method_calls_itself_recursively(
    lti13_config_environ: None,
    mock_nbgrader_helper: Mock,
    make_http_response: HTTPResponse,
    make_mock_request_handler: RequestHandler,
):

    headers = HTTPHeaders({
        'content-type': 'application/vnd.ims.lis.v2.lineitemcontainer+json',
        'link': '<https://learning.flatironschool.com/api/lti/courses/691/line_items?page=2&per_page=10>; rel=\'next\'',
    })

    local_handler = make_mock_request_handler(RequestHandler)
    sender = LTI13GradeSender('course-id', 'lab')

    lineitems_body_result = {
        'body': [ dict(id='value', scoreMaximum=0.0, label='label', resourceLinkId='abc') ],
        'headers': headers,
    }

    resp = [
        make_http_response(
            handler=local_handler.request, **lineitems_body_result
        ),
        make_http_response(
            handler=local_handler.request, body=lineitems_body_result['body']
        ),
    ]

    with patch.object(AsyncHTTPClient, 'fetch', side_effect=resp) as mock_fetch:

        # initial call then the method will detect
        # the Link header to get the next items
        await sender._get_lineitems_from_url('https://example.moodle.com/api/lti/courses/111/line_items')

        assert len(sender.all_lineitems) == 2

        assert mock_fetch.call_count == 2

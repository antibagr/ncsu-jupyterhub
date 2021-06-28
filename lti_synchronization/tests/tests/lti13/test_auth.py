import os
from unittest.mock import MagicMock, patch

import pem
import pytest
from moodle.lti13.auth import get_lms_access_token, get_pem_text_from_file
from tornado.httpclient import AsyncHTTPClient


def test_no_pem_file():
    '''
    Does get_pem_text_from_file raises PermissionError if a pem file is unavailable?
    '''

    with pytest.raises(PermissionError):
        get_pem_text_from_file('file.pem')


def test_empty_list_from_parse_file():
    '''
    Does get_pem_text_from_file raises Exception if parse_file returned empty list?
    '''

    with patch.object(pem, 'parse_file', return_value=[]):
        with pytest.raises(Exception):
            get_pem_text_from_file('file.pem')


@pytest.mark.slow
def test_parsing_pem_file(lti13_config_environ: None):
    '''
    Does get_pem_text_from_file calls parse_file and work properly?
    '''

    pem_key = os.environ.get('LTI13_PRIVATE_KEY')

    certs = pem.parse_file(pem_key)

    with patch.object(pem, 'parse_file', return_value=certs) as mock_parse:

        get_pem_text_from_file(pem_key)

        assert mock_parse.called


@pytest.mark.slow
@pytest.mark.asyncio
@patch('moodle.lti13.auth.get_pem_text_from_file')
@patch('moodle.lti13.auth.get_headers_to_jwt_encode')
async def test_get_lms_access_token(
    mock_get_headers_to_jwt: MagicMock,
    mock_get_pem_text: MagicMock,
    lti13_config_environ: None,
    mock_tornado_client: AsyncHTTPClient,
):
    '''
    Does get_lms_access_token call get_pem_text_from_file?
    '''

    pem_key = os.environ.get('LTI13_PRIVATE_KEY')

    mock_get_headers_to_jwt.return_value = None

    mock_get_pem_text.return_value = pem.parse_file(pem_key)[0].as_text()

    # here we're using a httpclient mocked
    await get_lms_access_token('url', pem_key, 'client-id')

    assert mock_get_pem_text.called

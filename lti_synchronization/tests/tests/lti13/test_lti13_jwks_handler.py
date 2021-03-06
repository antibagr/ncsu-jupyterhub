import os
import platform
from unittest.mock import patch

import pytest
from tornado.web import RequestHandler

from moodle.lti13.handlers import LTI13JWKSHandler


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason='No Windows support.')
def test_get_method_raises_permission_error_if_pem_file_is_protected(jwks_handler: LTI13JWKSHandler):
    '''
    Is a permission error raised if the private key is protected after calling the
    handler's method?
    '''

    # change pem permission
    key_path: str = str(os.environ.get('LTI13_PRIVATE_KEY'))

    os.chmod(key_path, 0o060)

    with pytest.raises(PermissionError):
        jwks_handler.get()


@pytest.mark.asyncio
async def test_get_method_raises_an_error_without_lti13_private_key(monkeypatch, jwks_handler: LTI13JWKSHandler):
    '''
    Is an environment error raised if the LTI13_PRIVATE_KEY env var is not set
    after calling the handler's method?
    '''

    monkeypatch.delenv('LTI13_PRIVATE_KEY')

    with pytest.raises(EnvironmentError):
        await jwks_handler.get()


@patch('tornado.web.RequestHandler.write')
def test_get_method_calls_write_method_with_a_dict(mock_write_method, jwks_handler: LTI13JWKSHandler):
    '''
    Does the write method is called with a dict?
    '''

    jwks_handler.get()

    assert mock_write_method.called

    write_args = mock_write_method.call_args[0]

    # make sure we're passing a dict to let tornado
    # convert it as json with the specific content-type
    assert write_args[0]
    assert type(write_args[0]) == dict


def test_get_method_set_content_type_as_json(jwks_handler: LTI13JWKSHandler):
    '''
    Does the write method is set the content-type header as application/json?
    '''

    jwks_handler.get()

    assert 'Content-Type' in jwks_handler._headers
    assert 'application/json' in jwks_handler._headers['Content-type']

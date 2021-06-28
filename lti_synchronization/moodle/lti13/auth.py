import json
import os
import time
import typing as t
import urllib
import uuid

import jwt
import pem
from Crypto.PublicKey import RSA
from jwcrypto.jwk import JWK
from loguru import logger
from moodle.utils import dump_json
from tornado.httpclient import AsyncHTTPClient, HTTPClientError


async def get_lms_access_token(
    token_endpoint: str,
    private_key_path: str,
    client_id: str,
    scope: t.Optional[str] = None,
) -> str:
    '''
    Gets an access token from the LMS Token endpoint
    by using the private key (pem format) and client id

    Args:
        token_endpoint (str): The url that will be used to make the request
        private_key_path (str): specify where the pem is
        client_id (str): For LTI 1.3 the Client ID that was obtained with the tool setup
        scope (type): . Defaults to None.

    Returns:
        str: A json with the token value

    '''

    def _get_params() -> t.Generator:
        '''
        Formatted parameters to send to logger.
        '''

        yield dump_json({k: str(v) for k, v in token_params.items()})
        yield token[-5:]
        yield dump_json({'scope': scope.split()})

        _dict = {**params, 'client_assertion': params['client_assertion'][-5:]}

        yield dump_json({k: str(v) for k, v in _dict.items()})

#         if 'f_exc' in globals():
#             yield f_exc.response.body if f_exc.response else f_exc.message
#         else:
#             yield json.loads(resp.body)
    logger.info('Token endpoint is: %s' % token_endpoint)

    token_params = {
        'iss': client_id,
        'sub': client_id,
        'aud': token_endpoint,
        'iat': int(time.time()) - 5,
        'exp': int(time.time()) + 60,
        'jti': str(uuid.uuid4()),
    }

    _params = _get_params()

    logger.debug('Getting lms access token with parameters\n%s' % next(_params))

    # get the pem-encoded content
    private_key = get_pem_text_from_file(private_key_path)

    headers = get_headers_to_jwt_encode(private_key)

    token = jwt.encode(token_params, private_key,
                       algorithm='RS256', headers=headers)

    logger.debug('Obtaining token %s' % next(_params))

    scope: str = scope or ' '.join([
        'https://purl.imsglobal.org/spec/lti-ags/scope/score',
        'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem',
        'https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly',
        'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly',
    ])

    logger.debug('Scope is %s' % next(_params))

    params = {
        'grant_type': 'client_credentials',
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': token,
        'scope': scope,
    }

    logger.debug('OAuth parameters are:\n\n%s' % next(_params))

    client = AsyncHTTPClient()

    body = urllib.parse.urlencode(params)

    try:
        resp = await client.fetch(token_endpoint, method='POST', body=body, headers=None)
    except HTTPClientError as f_exc:

        logger.info('Error by obtaining a token with lms. Detail: %s' % f_exc.response.body if f_exc.response else f_exc.message)
        raise

    else:
        logger.debug('Token response body is %s' % json.loads(resp.body))
        return json.loads(resp.body)


def get_jwk(public_key: str) -> dict:
    '''
    Load public key as dictionary

    Args:
        public_key (str): Path to pem

    Returns:
        dict: Exported public key

    '''

    jwk_obj = JWK.from_pem(public_key)

    public_jwk = json.loads(jwk_obj.export_public())

    public_jwk['alg'] = 'RS256'

    public_jwk['use'] = 'sig'

    return public_jwk


def get_headers_to_jwt_encode(private_key_text: str) -> t.Optional[dict]:
    '''
    Helper method that gets the dict headers to use in jwt.encode method

    Args:
        private_key_text (str): The PEM-Encoded content as text

    Returns:
        dict: A dict if the publickey can be exported or None otherwise

    '''

    public_key = RSA.importKey(private_key_text).publickey().exportKey()

    headers = None

    if public_key:

        jwk = get_jwk(public_key)

        headers = {'kid': jwk.get('kid')} if jwk else None

    return headers


def get_pem_text_from_file(private_key_path: str) -> str:
    '''
    Parses the pem file to get its value as unicode text.
    Check the pem permission, parse file generates
    a list of PEM objects and return plain text from it.

    Args:
        private_key_path (str): Path to the private key file.

    Returns:
        str: Text from PEM parsed file

    Raises:
        PermissionError: PEM File is not accessible
        ValueError: PEM file is invalid, no certificates found.
    '''

    if not os.access(private_key_path, os.R_OK):
        raise PermissionError()

    certs = pem.parse_file(private_key_path)

    if not certs:
        raise ValueError('Invalid pem file.')

    return certs[0].as_text()

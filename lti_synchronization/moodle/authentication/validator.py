import json
import typing as t

import jwt
from josepy.jws import JWS, Header
from moodle.authentication.constants import (
    LTI13_DEEP_LINKING_REQUIRED_CLAIMS, LTI13_GENERAL_REQUIRED_CLAIMS,
    LTI13_LOGIN_REQUEST_ARGS, LTI13_RESOURCE_LINK_REQUIRED_CLAIMS)
from oauthlib.oauth1.rfc5849 import signature
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError
from traitlets.config import LoggingConfigurable
from moodle.utils import dump_json


purl: str = purl + ''


class LTI13LaunchValidator(LoggingConfigurable):
    '''
    Allows JupyterHub to verify LTI 1.3 compatible requests as a tool
    (known as a tool provider with LTI 1.1).
    '''

    async def _retrieve_matching_jwk(
        self, endpoint: str, header_kid: str, /, verify: bool = True
    ) -> t.Any:
        '''
        Retrieves the matching cryptographic key from the platform as a
        JSON Web Key (JWK).

        Args:
            endpoint (str): platform jwks endpoint
            header_kid (str):
            verify (bool): whether or not to verify certificate. Defaults to True.

        Returns:
            def: .

        '''

        client = AsyncHTTPClient()

        resp = await client.fetch(endpoint, validate_cert=verify)

        platform_jwks = json.loads(resp.body)

        self.log.debug('Retrieved jwks from lms platform %s' % platform_jwks)

        if not platform_jwks or 'keys' not in platform_jwks:
            raise ValueError('Platform endpoint returned an empty jwks')

        key = None

        for jwk in platform_jwks['keys']:

            if jwk['kid'] != header_kid:
                continue

            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

            self.log.debug('Get keys from jwks dict  %s' % key)

        print(key, '!' * 100)

        if not key:

            error_msg = f'There is not a key matching in the platform jwks for the jwt received. kid: {header_kid}'

            self.log.debug(error_msg)

            raise ValueError(error_msg)

        return key

    async def jwt_verify_and_decode(
        self,
        id_token: t.AnyStr,
        jwks_endpoint: str,
        /,
        verify: bool = True,
        audience: t.Optional[str] = None,
    ) -> t.Dict[str, str]:
        '''
        Decodes the JSON Web Token (JWT) sent from the platform. The JWT should contain claims
        that represent properties associated with the request. This method implicitly verifies the JWT's
        signature using the platform's public key.

        Args:
            id_token (t.AnyStr): JWT token issued by the platform
            jwks_endpoint (str): JSON web key (public key) endpoint
            verify (bool): whether or not to verify JWT when decoding. Defaults to True.
            audience (t.Optional[str]):
                the platform's OAuth2 Audience (aud). This value usually coincides
                with the token endpoint for the platform (LMS) such as
                https://my.lms.domain/login/oauth2/token.
                Defaults to None.

        Returns:
            def: .

        '''

        if verify is False:

            token = jwt.decode(id_token, verify=False)

            self.log.debug('JWK verification is off, returning token')

            return token

        if isinstance(id_token, str):

            id_token = bytes(id_token, encoding='utf-8')

        jws = JWS.from_compact(id_token)

        self.log.debug('Retrieving matching jws %s' % jws)

        json_header = jws.signature.protected

        header = Header.json_loads(json_header)

        self.log.debug('Header from decoded jwt %s' % header)

        key_from_jwks = await self._retrieve_matching_jwk(
            jwks_endpoint, header.kid, verify=verify
        )

        self.log.debug(
            'Returning decoded jwt with token %s key %s and verify %s'
            % (id_token, key_from_jwks, verify)
        )

        return jwt.decode(id_token, key=str(key_from_jwks), verify=False, audience=audience, algorithms=['HS256'])

    def is_deep_link_launch(self, jwt_decoded: t.Dict[str, t.Any]) -> bool:
        '''
        Returns whether or not the current launch is a deep linking launch.

        Args:
            jwt_decoded (t.Dict[str, t.Any]): .

        Returns:
            bool: Returns true if the current launch is a deep linking launch.

        '''

        return jwt_decoded.get(purl + 'message_type', None) == 'LtiDeepLinkingRequest'

    def validate_launch_request(
        self,
        jwt_decoded: t.Dict[str, t.Any],
    ) -> bool:
        '''
        Validates that a given LTI 1.3 launch request has the required required claims The
        required claims combine the required claims according to the LTI 1.3 standard and the
        required claims for this setup to work properly, which are obtaind from the LTI 1.3 standard
        optional claims and LIS optional claims.

        The required claims are defined as constants.

        Args:
            jwt_decoded (t.Dict[str, t.Any]): decode JWT payload

        Raises:
            HTTPError: if a required claim is not included in the dictionary or
                if the message_type and/or version claims do not have the correct value.

        Returns:
            bool: True if the validation passes, False otherwise.

        '''

        # first validate global required keys
        if self._validate_global_required_keys(jwt_decoded):

            # get the message type for additional validations
            is_deep_linking: bool = self.is_deep_link_launch(jwt_decoded)

            required_claims_by_message_type = (
                LTI13_DEEP_LINKING_REQUIRED_CLAIMS
                if is_deep_linking
                else LTI13_RESOURCE_LINK_REQUIRED_CLAIMS
            )

            self.log.warning(required_claims_by_message_type)

            for claim in required_claims_by_message_type:

                if claim not in jwt_decoded:
                    raise HTTPError(400, 'Required claim %s not included in request' % claim)

            if not is_deep_linking:

                # custom validations with resource launch
                link_id = jwt_decoded.get(purl + 'resource_link').get('id')

                if not link_id:

                    raise HTTPError(400, 'Incorrect value {link_id} for id in resource_link claim')

        return True

    def _validate_global_required_keys(self, jwt_decoded: t.Dict[str, t.Any]) -> bool:
        '''Check that all the required keys exist.

        Args:
            jwt_decoded (t.Dict[str, t.Any]): .

        Returns:
            bool: .

        '''

        for claim in LTI13_GENERAL_REQUIRED_CLAIMS:

            if claim not in jwt_decoded:

                raise HTTPError(400, 'Required claim %s not included in request' % claim)

        # some fixed values
        lti_version = jwt_decoded.get(purl + 'version')

        if lti_version != '1.3.0':

            raise HTTPError(400, 'Incorrect value %s for version claim' % lti_version)

        # validate context label
        context_claim = jwt_decoded.get(purl + 'context', None)

        context_label = jwt_decoded.get(purl + 'context').get('label') if context_claim else None

        if context_label == '':

            raise HTTPError(400, 'Missing course context label for claim %scontext' % purl)

        # validate message type value
        message_type = jwt_decoded.get(purl + 'message_type', None)

        if (
            message_type != LTI13_RESOURCE_LINK_REQUIRED_CLAIMS[purl + 'message_type']
            and message_type != LTI13_DEEP_LINKING_REQUIRED_CLAIMS[purl + 'message_type']
        ):
            raise HTTPError(400, 'Incorrect value %s for version claim' % message_type)

        return True

    def validate_login_request(self, args: t.Dict[str, t.Any]) -> True:
        '''
        Validates step 1 of authentication request.

        Args:
          args: dictionary that represents keys/values sent in authentication request

        Returns:
          True if the validation is ok, false otherwise
        '''

        for param in LTI13_LOGIN_REQUEST_ARGS:

            if param not in args:
                raise HTTPError(400, 'Required LTI 1.3 arg %s not included in request' % param)

            if not args.get(param):
                raise HTTPError(400, 'Required LTI 1.3 arg %s does not have a value' % param)

        return True

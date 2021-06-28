import json
import os
import typing as t

from loguru import logger
from moodle.authentication.handlers import (LTI13CallbackHandler,
                                            LTI13LoginHandler)
from moodle.authentication.validator import LTI13LaunchValidator
from moodle.authentication.helper import LTIHelper
from moodle.typehints import JsonType
from oauthenticator.oauth2 import OAuthenticator
from jupyterhub.utils import url_path_join
from tornado.web import HTTPError
from traitlets import Unicode


class LTI13Authenticator(OAuthenticator):
    '''Custom authenticator used with LTI 1.3 requests'''

    login_service = 'LTI13Authenticator'

    # handlers used for login, callback, and jwks endpoints
    login_handler = LTI13LoginHandler

    callback_handler = LTI13CallbackHandler

    helper = LTIHelper()

    validator = LTI13LaunchValidator()

    # the client_id, authorize_url, and token_url config settings
    # are available in the OAuthenticator base class. they are overriden here
    # for the sake of clarity.
    client_id = Unicode(
        '',
        help='''
        The LTI 1.3 client id that identifies the tool installation with the
        platform.
        ''',
    ).tag(config=True)

    endpoint = Unicode(
        '',
        help='''
        The platform's base endpoint used when redirecting requests to the platform
        after receiving the initial login request.
        ''',
    ).tag(config=True)

    oauth_callback_url = Unicode(
        os.getenv('LTI13_CALLBACK_URL', ''),
        config=True,
        help='''Callback URL to use.
        Should match the redirect_uri sent from the platform during the
        initial login request.''',
    ).tag(config=True)

    async def authenticate(
                self,
                handler: LTI13LoginHandler,
                *_whatever: t.Any,
                **__whatever: t.Any,
            ) -> JsonType:
        '''
        Overrides authenticate from base class
        to handle LTI 1.3 authentication requests.

        Args:
            handler (LTI13LoginHandler): handler object
            **_ignored (t.Any)

        Returns:
            JsonType: Authentication dictionary

        '''

        purl: str = 'https://purl.imsglobal.org/spec/lti/claim'

        self.log.debug(f'JWKS platform endpoint is {self.endpoint}')

        # get jwks endpoint and token to use as
        # args to decode jwt. we could pass in
        # self.endpoint directly as arg to
        # jwt_verify_and_decode() but logging the
        id_token: str = handler.get_argument('id_token')

        self.log.debug(f'Got ID token issued by platform: {len(id_token)}')

        # extract claims from jwt (id_token)
        # sent by the platform. as tool use the jwks (public key)
        # to verify the jwt's signature.
        jwt_decoded = await self.validator.jwt_verify_and_decode(
            id_token,
            self.endpoint,
            verify=False,
            audience=self.client_id,
        )

        self.log.debug(f'Decoded JWT is {jwt_decoded}')

        if self.validator.validate_launch_request(jwt_decoded):

            jwt_course_id = jwt_decoded[f'{purl}/context']['label']

            course_id = self.helper.format_string(jwt_course_id)

            self.log.debug('Normalized course label is %s' % course_id)

            self.log.debug(json.dumps(jwt_decoded, indent=2))

            username = jwt_decoded[purl + '/ext']['user_username']

#             if 'email' in jwt_decoded and jwt_decoded['email']:
#                 username = self.helper.email_to_username(
#                     jwt_decoded['email'])
#             if 'name' in jwt_decoded and jwt_decoded['name']:
#                 username = jwt_decoded['name']
#             elif 'given_name' in jwt_decoded and jwt_decoded['given_name']:
#                 username = jwt_decoded['given_name']
#             elif 'family_name' in jwt_decoded and jwt_decoded['family_name']:
#                 username = jwt_decoded['family_name']
#             elif (
#                 f'{purl}/lis' in jwt_decoded
#                 and 'person_sourcedid'
#                 in jwt_decoded[f'{purl}/lis']
#                 and jwt_decoded[f'{purl}/lis']['person_sourcedid']
#             ):
#                 username = jwt_decoded[f'{purl}/lis']['person_sourcedid'].lower()
#
#             elif (
#                 'lms_user_id' in jwt_decoded[f'{purl}/custom']
#                 and jwt_decoded[f'{purl}/custom']['lms_user_id']
#             ):
#                 username = str(jwt_decoded[f'{purl}/custom']['lms_user_id'])

            # ensure the username is normalized
            self.log.debug('username is %s' % username)

            if username == '':
                raise HTTPError('Unable to set the username')

            # set role to learner role (by default)
            # if instructor or learner/student roles aren't
            # sent with the request
            user_role = 'Learner'

            for role in jwt_decoded[f'{purl}/roles']:

                if role.find('Instructor') >= 1:
                    user_role = 'Instructor'

                elif role.find('Learner') >= 1 or role.find('Student') >= 1:
                    user_role = 'Learner'

            self.log.debug('user_role is %s' % user_role)

            launch_return_url = ''

            if (
                f'{purl}/launch_presentation' in jwt_decoded
                and 'return_url' in jwt_decoded[f'{purl}/launch_presentation']
            ):
                launch_return_url = jwt_decoded[f'{purl}/launch_presentation']['return_url']

            lms_user_id = jwt_decoded['sub'] if 'sub' in jwt_decoded else username

            # ensure the user name is normalized
            # username_normalized = self.helper.format_string(username)
            #
            # self.log.debug('Assigned username is: %s' % username_normalized)

            return {
                'name': username,
                'auth_state': {
                    'course_id': course_id,
                    'user_role': user_role,
                    'lms_user_id': lms_user_id,
                    'launch_return_url': launch_return_url,
                },
            }

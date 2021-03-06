import hashlib
import os
import re
import uuid
import typing as t
from urllib.parse import quote, unquote, urlparse

from loguru import logger
from moodle.authentication.helper import LTIHelper
from moodle.authentication.validator import LTI13LaunchValidator
from moodle.utils import dump_json
from oauthenticator.oauth2 import (STATE_COOKIE_NAME, OAuthCallbackHandler,
                                   OAuthLoginHandler, _serialize_state,
                                   guess_callback_uri)
from tornado.httputil import url_concat
from tornado.web import HTTPError, RequestHandler


class LTI13LoginHandler(OAuthLoginHandler):
    '''
    Handles JupyterHub authentication requests according to the
    LTI 1.3 standard.
    '''

#     if os.getenv('DEBUG', 'True') == 'True':
#         log = logger

    def authorize_redirect(
        self,
        client_id: t.Optional[str] = None,
        login_hint: t.Optional[str] = None,
        lti_message_hint: t.Optional[str] = None,
        nonce: t.Optional[str] = None,
        redirect_uri: t.Optional[str] = None,
        state: t.Optional[str] = None,
        **_ignored,
    ) -> None:
        '''
        Overrides the OAuth2Mixin.authorize_redirect method to to initiate the LTI 1.3 / OIDC
        login flow. Arguments are redirected to the platform's authorization url for further
        processing.

        References:
        https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
        http://www.imsglobal.org/spec/lti/v1p3/#additional-login-parameters-0

        Args:
          client_id: used to identify the tool's installation with a platform
          redirect_uri: redirect url specified during tool installation (callback url)
          login_hint: opaque value used by the platform for user identity
          lti_message_hint: signed JWT which contains information needed to perform the
            launch including issuer, user and context information
          nonce: unique value sent to allow recipients to protect themselves against replay attacks
          state: opaque value for the platform to maintain state between the request and
            callback and provide Cross-Site Request Forgery (CSRF) mitigation.
        '''

        url = os.environ.get('LTI13_AUTHORIZE_URL')

        if not url:
            raise EnvironmentError('LTI13_AUTHORIZE_URL env var is not set')

        handler = t.cast(RequestHandler, self)

        args = {
            'response_type': 'id_token',
            'scope': 'openid',
            'extra_params': {},
            'response_mode': 'form_post',
            'prompt': 'none',
        }

        optional: set = {'client_id', 'login_hint',
                         'lti_message_hint', 'nonce', 'redirect_uri', 'state'}

        for arg in optional:

            if locals()[arg] is not None:
                args[arg] = locals()[arg]

        handler.redirect(url_concat(url, args))

    def get_state(self):

        next_url = original_next_url = self.get_argument('next', None)

        if not next_url:

            # try with the target_link_uri arg
            target_link = self.get_argument('target_link_uri', '')

            if 'next' in target_link:

                self.log.debug(
                    f'Trying to get the next-url from target_link_uri: {target_link}')

                next_search = re.search(
                    'next=(.*)', target_link, re.IGNORECASE)

                if next_search:

                    next_url = next_search.group(1)

                    # decode the some characters obtained with the link builder
                    next_url = unquote(next_url)

            elif not target_link.endswith('/hub'):
                next_url = target_link

        if next_url:

            # avoid browsers treating \ as /
            next_url = next_url.replace('\\', quote('\\'))

            # disallow hostname-having urls,
            # force absolute path redirect
            urlinfo = urlparse(next_url)

            next_url = urlinfo._replace(
                scheme='', netloc='', path='/' + urlinfo.path.lstrip('/')).geturl()

            if next_url != original_next_url:
                self.log.warning('Ignoring next_url %r, using %r',
                                 original_next_url, next_url)

        if self._state is None:

            self._state = _serialize_state(
                {
                    'state_id': uuid.uuid4().hex,
                    'next_url': next_url,
                }
            )

        return self._state

    def set_state_cookie(self, state):
        '''
        Overrides the base method to send the 'samesite' and 'secure'
        arguments and avoid the issues related with the use of iframes.
        It depends of python 3.8
        '''
        self.set_secure_cookie(
            STATE_COOKIE_NAME,
            state,
            expires_days=1,
            httponly=True,
            samesite=None,
            secure=True,
        )

    def post(self) -> None:
        '''
        Validates required login arguments sent from platform and then uses the
        authorize_redirect() method to redirect users to the authorization url.
        '''

        validator = LTI13LaunchValidator()

        args = LTIHelper.convert_request_to_dict(self.request.arguments)

        self.log.debug('Initial login request args are %s' % dump_json(
            {**args, 'lti_message_hint': args['lti_message_hint'][-5:]}))

        if validator.validate_login_request(args):

            login_hint = args['login_hint']

            self.log.debug('login_hint is %s' % login_hint)

            lti_message_hint = args['lti_message_hint']

            self.log.debug('lti_message_hint is %s' % lti_message_hint[-5:])

            client_id = args['client_id']

            self.log.debug('client_id is %s' % client_id)

            redirect_uri = guess_callback_uri(
                'https', self.request.host, self.hub.server.base_url)

            self.log.info('redirect_uri: %s' % redirect_uri)

            state = self.get_state()

            self.set_state_cookie(state)

            # TODO: validate that received nonces haven't been received before
            # and that they are within the time-based tolerance window

            nonce_raw = hashlib.sha256(state.encode())

            nonce = nonce_raw.hexdigest()

            self.authorize_redirect(
                client_id=client_id,
                login_hint=login_hint,
                lti_message_hint=lti_message_hint,
                nonce=nonce,
                redirect_uri=redirect_uri,
                state=state,
            )


class LTI13CallbackHandler(OAuthCallbackHandler):
    '''
    LTI 1.3 call back handler
    '''

    async def post(self):
        '''
        Overrides the upstream get handler with it's standard implementation.
        '''

        self.check_state()

        user = await self.login_user()

        self.log.debug(f'user logged in: {user}')

        if user is None:
            raise HTTPError(403, 'User missing or null')

        self.redirect(self.get_next_url(user))

        self.log.debug('Redirecting user %s to %s' %
                       (user.id, self.get_next_url(user)))

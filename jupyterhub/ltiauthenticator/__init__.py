import logging
import os
import time
from collections import OrderedDict
from datetime import datetime

from oauthlib.oauth1.rfc5849 import signature
from tornado import gen, web
from traitlets import Dict

from jupyterhub.auth import Authenticator, LocalAuthenticator
from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join

__version__ = '1.0.0'


class LTILaunchValidator:
    # Record time when process starts, so we can reject requests made
    # before this
    PROCESS_START_TIME = int(time.time())

    # Keep a class-wide, global list of nonces so we can detect & reject
    # replay attacks. This possibly makes this non-threadsafe, however.
    nonces = OrderedDict()

    def __init__(self, consumers):
        self.consumers = consumers

    def validate_launch_request(
            self,
            launch_url,
            headers,
            args
    ):
        """
        Validate a given launch request

        launch_url: Full URL that the launch request was POSTed to
        headers: k/v pair of HTTP headers coming in with the POST
        args: dictionary of body arguments passed to the launch_url
            Must have the following keys to be valid:
                oauth_consumer_key, oauth_timestamp, oauth_nonce,
                oauth_signature
        """

        # Validate args!

        if 'oauth_consumer_key' not in args:
            raise web.HTTPError(401, "oauth_consumer_key missing")
        if args['oauth_consumer_key'] not in self.consumers:
            raise web.HTTPError(401, "oauth_consumer_key not known")

        if 'oauth_signature' not in args:
            raise web.HTTPError(401, "oauth_signature missing")
        if 'oauth_timestamp' not in args:
            raise web.HTTPError(401, 'oauth_timestamp missing')

        # Allow 30s clock skew between LTI Consumer and Provider
        # Also don't accept timestamps from before our process started, since that could be
        # a replay attack - we won't have nonce lists from back then. This would allow users
        # who can control / know when our process restarts to trivially do replay attacks.
        oauth_timestamp = int(float(args['oauth_timestamp']))
        if (
                int(time.time()) - oauth_timestamp > 30
                or oauth_timestamp < LTILaunchValidator.PROCESS_START_TIME
        ):
            raise web.HTTPError(401, "oauth_timestamp too old")

        if 'oauth_nonce' not in args:
            raise web.HTTPError(401, 'oauth_nonce missing')
        if (
                oauth_timestamp in LTILaunchValidator.nonces
                and args['oauth_nonce'] in LTILaunchValidator.nonces[oauth_timestamp]
        ):
            raise web.HTTPError(
                401, "oauth_nonce + oauth_timestamp already used")
        LTILaunchValidator.nonces.setdefault(
            oauth_timestamp, set()).add(args['oauth_nonce'])

        args_list = []
        for key, values in args.items():
            if type(values) is list:
                args_list += [(key, value) for value in values]
            else:
                args_list.append((key, values))

        base_string = signature.signature_base_string(
            'POST',
            signature.base_string_uri(launch_url),
            signature.normalize_parameters(
                signature.collect_parameters(body=args_list, headers=headers)
            )
        )

        consumer_secret = self.consumers[args['oauth_consumer_key']]

        sign = signature.sign_hmac_sha1(base_string, consumer_secret, None)
        is_valid = signature.safe_string_equals(sign, args['oauth_signature'])

        if not is_valid:
            raise web.HTTPError(401, "Invalid oauth_signature")
        return True


class LTIAuthenticator(Authenticator):
    """
    JupyterHub Authenticator for use with LTI based services (EdX, Canvas, etc)
    """

    auto_login = True
    login_service = 'LTI'

    consumers = Dict(
        {},
        config=True,
        help="""
        A dict of consumer keys mapped to consumer secrets for those keys.

        Allows multiple consumers to securely send users to this JupyterHub
        instance.
        """
    )

    def get_handlers(self, app):
        return [
            ('/lti/launch', LTIAuthenticateHandler)
        ]

    @gen.coroutine
    def authenticate(self, handler, data=None):
        # FIXME: Run a process that cleans up old nonces every other minute
        validator = LTILaunchValidator(self.consumers)

        args = {}
        for k, values in handler.request.body_arguments.items():
            args[k] = values[0].decode() if len(values) == 1 else [
                                       v.decode() for v in values]

        # handle multiple layers of proxied protocol (comma separated) and take the outermost
        if 'x-forwarded-proto' in handler.request.headers:
            # x-forwarded-proto might contain comma delimited values
            # left-most value is the one sent by original client
            hops = [h.strip()
                    for h in handler.request.headers['x-forwarded-proto'].split(',')]
            protocol = hops[0]
        else:
            protocol = handler.request.protocol

        launch_url = protocol + "://" + handler.request.host + handler.request.uri

        self.log.warning(f"{args}\n{handler.request.headers}")

        if validator.validate_launch_request(
                launch_url,
                handler.request.headers,
                args
        ):
            user_role = "Learner"
            if "roles" in args and args["roles"]:
                args["role"] = args["roles"].split(",")[0]
                self.log.debug("User LTI role is: %s" % user_role)
            else:
                raise HTTPError(
                    400, "User role not included in the LTI request")

            user_name = handler.get_body_argument('ext_user_username')

            return {
                'name': user_name,
                'auth_state': {k: v for k, v in args.items() if not k.startswith('oauth_')}
            }

    def login_url(self, base_url):
        return url_path_join(base_url, '/lti/launch')


class LTIAuthenticateHandler(BaseHandler):
    """
    Handler for /lti/launch

    Implements v1 of the LTI protocol for passing authentication information
    through.

    If there's a custom parameter called 'next', will redirect user to
    that URL after authentication. Else, will send them to /home.
    """

    def set_login_cookie(self, user):
        super().set_login_cookie(user)
        self.set_hub_cookie(user)

    @gen.coroutine
    def post(self):

        _ = yield self.login_user()
        next_url = self.get_next_url()
        body_argument = self.get_body_argument(
            name='custom_next',
            default=next_url,
        )

        self.redirect(body_argument)

import os
from unittest.mock import MagicMock

from jupyterhub.spawner import LocalProcessSpawner

# mocking c variable in dev environment
if os.getenv('DEBUG', 'True') == 'True':
    c = MagicMock()

# ---------------
# IP
# ---------------

c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.port = 443

c.JupyterHub.tornado_settings = {
    'headers': {
        'Content-Security-Policy': 'frame-ancestors \'self\' *'
    },
    'cookie_options': {
        'SameSite': 'None',
        'Secure': True
    },
}

c.JupyterHub.allow_root = True
c.JupyterHub.allow_origin = '*'

# ---------------
# SSL
# ---------------

c.JupyterHub.ssl_cert = os.getenv('SSL_CERT_PATH', None)
c.JupyterHub.ssl_key = os.getenv('SSL_KEY_PATH', None)

# ---------------
# DIRECTORY
# ---------------

MODULE_NAME: str = 'lti_synchronization.moodle'

DOMAIN: str = 'https://jhub-dev.cos.ncsu.edu'

# ---------------
# AUTHENTICAION
# ---------------

c.JupyterHub.authenticator_class = f'{MODULE_NAME}.LTI13Authenticator'

c.LTI13Authenticator.endpoint = os.environ.get(
    'LTI13_ENDPOINT',
    '0.0.0.0:443/hub/lti/login',
)

c.LTI13Authenticator.client_id = os.environ.get('LTI13_CLIENT_ID')

c.LTI13Authenticator.authorize_url = os.environ.get(
    'LTI13_AUTHORIZE_URL',
    f'{DOMAIN}/lti/authorize_redirect'
)

c.LTI13Authenticator.token_url = os.environ.get(
    'LTI13_TOKEN_URL',
    f'{DOMAIN}/login/oauth2/token'
)

c.JupyterHub.extra_handlers = [
  (r'/lti13/config$', f'{MODULE_NAME}.lti13.handlers.LTI13ConfigHandler'),
  (r'/lti13/jwks$', f'{MODULE_NAME}.lti13.handlers.LTI13JWKSHandler'),
  (r'/submit-grades/(?P<course_id>\w+)/(?P<assignment_name>\w+)',
   f'{MODULE_NAME}.grades.handlers.SendGradesHandler'),
]

c.Authenticator.enable_auth_state = True

c.LocalAuthenticator.auto_login = True

c.LocalAuthenticator.create_system_users = True

# ---------------
# SPAWNER
# ---------------

c.JupyterHub.spawner_class = LocalProcessSpawner

c.Spawner.args = ['--debug', ]

c.LocalProcessSpawner.shell_cmd = ['bash', '-l', '-c']


def pre_spawn_hook(spawner) -> None:

    spawner.log.warning(f'Spawning {spawner.user.name}')


def bind_auth_state(spawner, auth_state: dict) -> None:

    spawner.log.info('Bind auth state to a spawner.')

    spawner.userdata = auth_state


c.JupyterHub.spawner_class = LocalProcessSpawner

c.Spawner.auth_state_hook = bind_auth_state

c.Spawner.pre_spawn_hook = pre_spawn_hook

c.Spawner.args = ['--allow-root']

# ---------------
# USERS
# ---------------

c.JupyterHub.admin_access = True

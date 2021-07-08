import os
from typing import List
from unittest.mock import MagicMock

from jupyterhub.spawner import LocalProcessSpawner

from lti_synchronization.moodle.integration import system

# mocking c variable in dev environment
if os.getenv('DEBUG', 'True') == 'True':
    c = MagicMock()

c.JupyterHub.log_level = 'DEBUG'

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

c.JupyterHub.authenticator_class = 'lti_synchronization.moodle.LTI13Authenticator'

c.LTI13Authenticator.client_id = os.environ.get('LTI13_CLIENT_ID')

# 'LTI13_ENDPOINT'
c.LTI13Authenticator.endpoint = os.getenv('LTI13_ENDPOINT')

# 'LTI13_AUTHORIZE_URL'
c.LTI13Authenticator.authorize_url = os.getenv('LTI13_AUTHORIZE_URL')

# 'LTI13_TOKEN_URL',
c.LTI13Authenticator.token_url = os.getenv('LTI13_TOKEN_URL')

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

LOCAL_UNIX_USERS: List[str] = []


def pre_spawn_hook(spawner) -> None:
    '''Short summary.

    Args:
        spawner: .

    '''

    global LOCAL_UNIX_USERS

    raise Exception(type(spawner))

    username: str = spawner.user.name

    spawner.log.warning(f'Spawning server for {username!r}')

    if username not in LOCAL_UNIX_USERS:

        spawner.log.info(f'Creating UNIX user for {username!r}')

        system.create_user(username)
        system.chown(username, f'/home/{username}')

    LOCAL_UNIX_USERS = system.get_unix_usernames()


def bind_auth_state(spawner, auth_state: dict) -> None:
    '''Short summary.

    Args:
        spawner: .
        auth_state: .

    '''

    spawner.log.info(f'{type(spawner)} {type(auth_state)}')

    spawner.userdata = auth_state


c.JupyterHub.spawner_class = LocalProcessSpawner

c.Spawner.auth_state_hook = bind_auth_state

c.Spawner.pre_spawn_hook = pre_spawn_hook

c.Spawner.args = ['--allow-root']

# ---------------
# USERS
# ---------------

c.JupyterHub.admin_access = True

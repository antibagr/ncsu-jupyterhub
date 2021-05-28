import json
import os
import platform
import pwd
import subprocess
from os import path
from unittest.mock import Mock

from jupyterhub.spawner import LocalProcessSpawner

# mocking c variable while
# editing the file to turn off linter.
if platform.system() == 'Windows':
    c = Mock()
# ---------------
# IP
# ---------------

c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.port = 443

c.JupyterHub.tornado_settings = {
    "headers": {"Content-Security-Policy": "frame-ancestors 'self' *"},
    "cookie_options": {"SameSite": "None", "Secure": True},
}

c.JupyterHub.allow_root = True
c.JupyterHub.allow_origin = "*"

# ---------------
# SSL
# ---------------

c.JupyterHub.ssl_cert = '/srv/jupyterhub/ssc_jhub.crt'
c.JupyterHub.ssl_key = '/srv/jupyterhub/ssc_jhub.key'

# ---------------
# DIRECTORY
# ---------------

BASE_DIR: str = '/srv/jupyterhub'

# c.CourseDirectory.root = BASE_DIR

# ---------------
# AUTHENTICAION
# ---------------

c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

c.LTIAuthenticator.consumers = {
    os.getenv('LTI_CONSUMER_KEY'): os.getenv('LTI_CONSUMER_SECRET'),
}

c.Authenticator.enable_auth_state = True

c.LocalAuthenticator.auto_login = True

c.LocalAuthenticator.create_system_users = True

# ---------------
# SPAWNER
# ---------------

c.JupyterHub.spawner_class = LocalProcessSpawner

c.Spawner.args = ['--debug', ]

c.LocalProcessSpawner.shell_cmd = ['bash', '-l', '-c']


def pre_spawn_hook(spawner):

    username = spawner.user.name

    os.system(f'useradd -m {username}')
    os.system(f'export XDG_RUNTIME_DIR="" && chmod -R 777 /home/{username} && chown -R {username} /home/{username}')

    spawner.log.warning(
        json.dumps(spawner.userdata or {
                   'Data': 'Not Found'}, indent=4, sort_keys=True, ensure_ascii=False)
    )


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

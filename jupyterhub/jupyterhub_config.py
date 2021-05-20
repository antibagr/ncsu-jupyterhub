import os
import platform
import pwd
import subprocess
from os import path
from unittest.mock import Mock

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

# ---------------
# SSL
# ---------------

c.JupyterHub.ssl_cert = '/srv/jupyterhub/ssc_jhub.crt'
c.JupyterHub.ssl_key = '/srv/jupyterhub/ssc_jhub.key'

# ---------------
# DIRECTORY
# ---------------

BASE_DIR: str = '/srv/jupyterhub'

c.CourseDirectory.root = BASE_DIR

# c.JupyterHub.extra_log_file = path.join(BASE_DIR, 'jupyterhub.log')


# ---------------
# AUTHENTICAION
# ---------------

c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

c.LTIAuthenticator.consumers = {
    os.getenv('LTI_CONSUMER_KEY'): os.getenv('LTI_CONSUMER_SECRET'),
}

c.Authenticator.enable_auth_state = True

# ---------------
# USERS
# ---------------

c.JupyterHub.admin_users = set()

c.JupyterHub.admin_access = True


# ---------------
# SPAWNER
# ---------------

c.JupyterHub.spawner_class = 'simplespawner.SimpleLocalProcessSpawner'

c.SimpleLocalProcessSpawner.home_path_template = '/home/{username}'

# c.SystemdSpawner.dynamic_users = True

# c.SystemdSpawner.readwrite_paths = ['/srv/nbgrader/exchange']


# c.Spawner.notebook_dir = '~/notebooks'

c.Spawner.args = ['--debug', ]


def pre_spawn_hook(spawner):

    username = spawner.user.name

#    try:
#        pwd.getpwnam(username)
#    except KeyError:
#        subprocess.check_call(['useradd', '-ms', '/bin/bash', username])

    if not os.path.exists(f'/home/{username}'):
        os.makedirs(f'/home/{username}')

    if spawner.userdata['role'] == 'Instructor':
       if not os.path.exists(f'/home/{username}/nbgrader_config.py'):
           spawner.log.info(
               'Initialize instructor\'s directory. Create nbgrader_config and test course')
           with open(f'/home/{username}/nbgrader_config.py', 'w') as f:
               f.write(f'''
c = get_config()

c.CourseDirectory.root = "/home/{username}/test_course"

c.Exchange.path_includes_course = True
''')
           os.system(f'cd /home/{username} && nbgrader quickstart test_course')
       # subprocess.check_call(f'su - {username} && jupyter serverextension disable --user nbgrader.server_extensions.formgrader'.split())

    spawner.log.warning(spawner.userdata or 'NO AUTH STATE FOUND')


def bind_auth_state(spawner, auth_state: dict) -> None:
    spawner.log.info('bind auth state to a spawner')
    spawner.userdata = auth_state


c.Spawner.auth_state_hook = bind_auth_state

c.Spawner.pre_spawn_hook = pre_spawn_hook

c.Spawner.args = ['--allow-root']

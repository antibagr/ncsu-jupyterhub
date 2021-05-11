import os
from os import path
import platform

from unittest.mock import Mock


# mocking c variable while editing the file to turn off linter.
if platform.system() == 'Windows': c = Mock()

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

c.JupyterHub.spawner_class = 'systemdspawner.SystemdSpawner'

c.SystemdSpawner.dynamic_users = True

c.SystemdSpawner.readwrite_paths = ['/srv/nbgrader/exchange']


# c.Spawner.notebook_dir = '~/notebooks'

c.Spawner.args = ['--debug',]

def pre_spawn_hook(spawner):

    import pwd
    import subprocess
    import os

    username = spawner.user.name

#    try:
#        pwd.getpwnam(username)
#    except KeyError:
#        subprocess.check_call(['useradd', '-ms', '/bin/bash', username])

    with open(f'/home/{username}/nbgrader_config.py', 'w') as f:
        f.write('''
c = get_config()
c.CourseDirectory.course_id = "test_course"
c.Exchange.root = "/srv/nbgrader/exchange"
''')
#     if spawner.userdata['role'] != 'Instructor':
       # subprocess.check_call(f'jupyter nbextension disable --user formgrader/main --section=tree')
       # subprocess.check_call(f'su - {username} && jupyter serverextension disable --user nbgrader.server_extensions.formgrader'.split())


    spawner.log.warning(spawner.userdata or 'NO AUTH STATE FOUND')


def bind_auth_state(spawner, auth_state: dict) -> None:
    spawner.log.info('bind auth state to a spawner')
    spawner.userdata = auth_state



# c.Spawner.auth_state_hook = bind_auth_state

# c.Spawner.pre_spawn_hook = pre_spawn_hook

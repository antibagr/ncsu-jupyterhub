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

# c.SystemdSpawner.dynamic_users = True

# c.SystemdSpawner.readwrite_paths = ['/srv/nbgrader/exchange']


# c.Spawner.notebook_dir = '~/notebooks'

c.Spawner.args = ['--debug', ]

c.Authenticator.whitelist = {'student', 'test_student3', 'api_admin', 'test_teacher', 'test_ta', 'admin', 'test_student2', 'test_student'}

c.Authenticator.admin_users = {'admin', 'api_admin'}

c.JupyterHub.load_groups = {'formgrade-second_course': ['admin', 'api_admin', 'test_ta', 'grader-second_course'], 'formgrade-first_course': ['test_student3', 'test_teacher', 'grader-first_course']}

c.JupyterHub.services = [{'name': 'your_school', 'url': 'http://127.0.0.1:9999', 'command': ['jupyterhub-singleuser', '--group=formgrade-your_school', '--debug'], 'user': 'grader-your_school', 'cwd': '/home/grader-your_school', 'api_token': 'cb50e05c10775855e8a48319d68014777f4d9573281ec1958ceed6a32c0f369b'}, {'name': 'second_course', 'url': 'http://127.0.0.1:9999', 'command': ['jupyterhub-singleuser', '--group=formgrade-second_course', '--debug'], 'user': 'grader-second_course', 'cwd': '/home/grader-second_course', 'api_token': '80461909f950b6cb8ab98483ad6e44cbad18cc0d48c0bd072920c39824dce43a'}, {'name': 'first_course', 'url': 'http://127.0.0.1:9999', 'command': ['jupyterhub-singleuser', '--group=formgrade-first_course', '--debug'], 'user': 'grader-first_course', 'cwd': '/home/grader-first_course', 'api_token': '3d988e7b4ede883d6d41dcfd8fe0edd28bb55f783600455a56883fe5dc204ed9'}]

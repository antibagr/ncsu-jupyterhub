import os
from os import path
import platform

from unittest.mock import Mock


# mocking c variable while editing the file to turn off linter.
if platform.system() == 'Windows': c = Mock()

# ---------------
# IP
# ---------------

# c.JupyterHub.bind_url = 'https://jhub-dev.cos.ncsu.edu:443'
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.port = 443

# ---------------
# SSL
# ---------------

c.JupyterHub.ssl_cert = '/etc/ssl/certs/ssc_jhub.crt'
c.JupyterHub.ssl_key = '/etc/ssl/private/ssc_jhub.key'

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

# ---------------
# USERS
# ---------------

c.JupyterHub.admin_users = set()

c.JupyterHub.admin_access = False

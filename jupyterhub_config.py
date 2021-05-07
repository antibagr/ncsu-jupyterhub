import os
import platform

from unittest.mock import Mock


# mocking c variable while editing the file to turn off linter.
if platform.system() == 'Windows': c = Mock()

# ---------------
# IP
# ---------------

c.JupyterHub.bind_url = 'https://jhub-dev.cos.ncsu.edu:443'
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

c.CourseDirectory.root = '/srv/jupyterhub'

# ---------------
# AUTHENTICAION
# ---------------

c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

c.LTIAuthenticator.consumers = {
    os.getenv('consume_key'): os.getenv('consume_secret'),
}

# ---------------
# USERS
# ---------------

c.JupyterHub.admin_users = {}

c.JupyterHub.admin_access = True

# c.LocalAuthenticator.create_system_users=True

# c.JupyterHub.admin_access = True
# import os

# c.JupyterHub.spawner_class = 'dockerspawner.SwarmSpawner'
# network_name = os.environ['DOCKER_NETWORK_NAME']
# c.SwarmSpawner.network_name = network_name
# c.SwarmSpawner.extra_host_config = {'network_mode': network_name}

# c.DockerSpawner.host_ip = "0.0.0.0"

# c.JupyterHub.ssl_key = 'key.pem'
c.JupyterHub.ssl_cert = 'certificate.crt'
c.JupyterHub.ssl_key = 'key.key'

c.CourseDirectory.root = '/srv/jupyterhub/test_course/source'

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.port = 443

c.JupyterHub.bind_url = 'https://jhub-dev.cos.ncsu.edu:443'

c.JupyterHub.spawner_class = 'simplespawner.SimpleLocalProcessSpawner' # 'sudospawner.SudoSpawner' # 'simplespawner.SimpleLocalProcessSpawner'

c.Spawner.args = ['--allow-root']

c.JupyterHub.ip = '0.0.0.0'

c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

c.LTIAuthenticator.consumers = {'9376ace600c133f074c4482eb8035ea1b32280e969576cf2df9b75ca05033eb4': '03f1f6119177781dcf7540289708fe426be57a26b44628b0f867dee8ba2373e1'}

c.JupyterHub.admin_users = { '1', '2', '3', '4' }

c.JupyterHub.admin_access = True

c.LocalAuthenticator.create_system_users=True

# c.JupyterHub.spawner_class = 'dockerspawner.SystemUserSpawner'

# c.DockerSpawner.host_ip = "0.0.0.0"

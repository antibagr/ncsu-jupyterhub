# c.LocalAuthenticator.create_system_users=True

# c.JupyterHub.admin_access = True
# import os

# c.JupyterHub.spawner_class = 'dockerspawner.SwarmSpawner'
# network_name = os.environ['DOCKER_NETWORK_NAME']
# c.SwarmSpawner.network_name = network_name
# c.SwarmSpawner.extra_host_config = {'network_mode': network_name}

# c.DockerSpawner.host_ip = "0.0.0.0"

c.JupyterHub.hub_ip = '0.0.0.0'

c.JupyterHub.spawner_class = 'simplespawner.SimpleLocalProcessSpawner'
c.Spawner.args = ['--allow-root']

c.JupyterHub.ip = '0.0.0.0'

c.JupyterHub.port = 8000

c.JupyterHub.authenticator_class = 'ltiauthenticator.LTIAuthenticator'

c.LTIAuthenticator.consumers = {
    "846d620d84d83153495cd2d28e239405ff13887b1a1d9957a71160eceed9e1d6": "fabfd9ca0dbb69f1cd4d2d77c413a112fb83069b8ea2b211062ec79ee411579e"
}

c.JupyterHub.admin_users = { '1', '2', '3', '4' }

c.JupyterHub.admin_access = True

# c.JupyterHub.spawner_class = 'dockerspawner.SystemUserSpawner'

# c.DockerSpawner.host_ip = "0.0.0.0"


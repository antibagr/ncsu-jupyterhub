from nbgrader.auth import JupyterHubAuthPlugin

c = get_config()

c.Exchange.root = "/srv/nbgrader/exchange"

c.HubAuth.hub_base_url = "https://jhub-dev.cos.ncsu.edu:443"

c.HubAuth.hub_port = 443

c.Exchange.path_includes_course = True

# c.Authenticator.plugin_class = JupyterHubAuthPlugin

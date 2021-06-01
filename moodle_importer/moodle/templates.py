class Config:
    '''
    Storage for the configuration templates.
    '''

    home_config: str = """
c = get_config()

c.CourseDirectory.root = '/home/{grader}/{course_id}'
c.CourseDirectory.db_url = '{db_url}'
c.CourseDirectory.course_id = '{course_id}'
"""

    course_config: str = """
c = get_config()

c.CourseDirectory.course_id = '{course_id}'
"""


NBGRADER_HOME_CONFIG_TEMPLATE_SHORT = """
c = get_config()
c.CourseDirectory.db_url = '{db_url}'
"""

JUPYTERHUB_USERS = """
c.LTIAuthenticator.allowed_users = {whitelist}

c.Authenticator.admin_users = {admin_users}

c.JupyterHub.load_groups = {groups}

c.JupyterHub.services = {services}

c.JupyterHub.api_tokens = {tokens}
"""

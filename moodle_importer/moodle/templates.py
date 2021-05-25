NBGRADER_HOME_CONFIG_TEMPLATE = """
c = get_config()

c.CourseDirectory.root = '/home/{grader_name}/{course_id}'
c.ClearSolutions.code_stub = {{
    "python": "# your code here\\nraise NotImplementedError",
    "javascript": "// your code here\\nthrow new Error();",
    "julia": "# your code here\\nthrow(ErrorException())"
}}
c.CourseDirectory.db_url = '{db_url}'
"""

NBGRADER_HOME_CONFIG_TEMPLATE_SHORT = """
c = get_config()
c.CourseDirectory.db_url = '{db_url}'
"""


NBGRADER_COURSE_CONFIG_TEMPLATE = """
c = get_config()

c.CourseDirectory.course_id = '{course_id}'
# c.IncludeHeaderFooter.header = 'source/header.ipynb'
# c.IncludeHeaderFooter.footer = 'source/footer.ipynb'
"""

JUPYTERHUB_USERS = """
c.LTIAuthenticator.allowed_users = {whitelist}

c.Authenticator.admin_users = {admin_users}

c.JupyterHub.load_groups = {groups}

c.JupyterHub.services = {services}

c.JupyterHub.api_tokens = {tokens}

"""

from loguru import logger

from moodle.utils import grader
from moodle.templates import (NBGRADER_COURSE_CONFIG_TEMPLATE,
                              NBGRADER_HOME_CONFIG_TEMPLATE,
                              NBGRADER_HOME_CONFIG_TEMPLATE_SHORT)


class Templater:

    @staticmethod
    def create_service(course_id: str, api_token: str, port: int = 0) -> dict:
        return {
            'name': course_id,
            "admin": True,
            'url': f'http://127.0.0.1:{9000 + port}',
            'command': [
                'jupyterhub-singleuser',
                f'--group=formgrade-{course_id}',
                '--debug',
                '--allow-root',
            ],
            'user': f'grader-{course_id}',
            'cwd': f'/home/grader-{course_id}',
            'api_token': api_token,
            'environment': {'JUPYTERHUB_SERVICE_USER': f'grader-{course_id}'}
        }

    @staticmethod
    def write_grader_config(course_id: str) -> None:

        course_grader: str = grader / course_id

        logger.debug(f'Writing grader config for {course_grader}')

        with open(f'/home/{grader / course_id}/.jupyter/nbgrader_config.py', 'w') as f:
            f.write(
                NBGRADER_HOME_CONFIG_TEMPLATE.format(
                    grader=grader / course_id,
                    course_id=course_id,
                    db_url='sqlite:///' + f'/home/{course_grader}/grader.db'
                )
            )

        with open(f'/home/{course_grader}/{course_id}/nbgrader_config.py', 'w') as f:
            f.write(
                NBGRADER_COURSE_CONFIG_TEMPLATE.format(course_id=course_id)
            )

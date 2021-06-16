import os
import typing as t

from loguru import logger
from .templates import Config
from moodle.typehints import PathLike
from moodle.utils import JsonDict, grader
from yapf.yapflib.yapf_api import FormatCode


class Templater:
    '''
    Class for working with configuration files and filling templates.

    Public methods:

        create_service
        write_nbgrader_config
    '''

    def get_default(self, file_path: PathLike) -> str:
        '''Short summary.

        Args:
            file_path (PathLike): .

        Returns:
            str: .

        '''

        if not os.path.exists(file_path):
            raise OSError(f'Template file {file_path!r} does not exists!')

        if os.stat(file_path).st_size == 0:
            raise OSError(f'Template file {file_path!r} file is empty.')

        with open(file_path, 'r') as f:
            return f.read()

    def update_jupyterhub_config(
        self,
        file_path: PathLike,
        default_config: str,
        **kwargs: t.Any
    ) -> None:
        '''Short summary.

        Args:
            file_path (PathLike): .
            default_config (str): .
            **kwargs (t.Any): .

        Returns:
            None: .

        '''

        if os.path.exists(file_path):

            logger.warning(f'Old {file_path!r} will be overwritten.')

        with open(file_path, 'w') as jupyterhub_config:

            jupyterhub_config.write(
                FormatCode(
                    Config.template_warning
                    + '\n\n\n'
                    + default_config
                    + Config.users.format(**kwargs), style_config='pep8'
                )[0]
            )

        logger.info(f'Successfully updated {file_path!r}')

    @staticmethod
    def create_service(course_id: str, api_token: str, port: int = 0) -> JsonDict:
        '''
        Fills service template with provided data.

        Args:
            course_id (str): Normalized course's name.
            api_token (str): Jupyterhub Service API token.
            port (int): Port to run service on. Defaults to 0.

        Returns:
            JsonDict: Dict that you can add to services in jupyterhub_config.py
        '''

        return JsonDict({
            'name': course_id,
            'admin': True,
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
        })

    @staticmethod
    def write_grader_config(course_id: str) -> None:
        '''
        In order to set up course, we need to create two configuration files.

        1. /home/grader-course_id/.jupyter/nbgrader_config.py

            Default 'home' configuration in hidden folder.
            Points to course's root directory, course id and database URI.

        2. /home/grader-course_id/course_id/nbgrader_config.py

            Config inside the course root sets up course_id one more time.

        Args:
            course_id (str): Normalized name of the course
        '''

        course_grader: str = grader / course_id

        logger.debug(f'Writing grader config for {course_grader}')

        with open(f'/home/{course_grader}/.jupyter/nbgrader_config.py', 'w') as f:
            f.write(
                Config.home_config.format(
                    grader=grader / course_id,
                    course_id=course_id,
                    db_url='sqlite:///' + f'/home/{course_grader}/grader.db'
                )
            )

        with open(f'/home/{course_grader}/{course_id}/nbgrader_config.py', 'w') as f:
            f.write(
                Config.course_config.format(course_id=course_id)
            )

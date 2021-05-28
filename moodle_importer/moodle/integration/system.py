import os
import typing as t

from loguru import logger

from moodle.typehints import PathLike


Dirs = t.List[PathLike]


def join_dirs(*dirs: Dirs) -> str:
    return ' '.join(list(map(str, dirs)))


class SystemCommand:

    def create_dirs(self, *dirs: Dirs) -> None:

        # make unrelated directories
        # in contrast with os.mkdirs
        os.system(f'mkdir -p {join_dirs(dirs)}')

        logger.debug(f'Create {len(dirs)} directories: {join_dirs(dirs)}.')

    def create_database(self, grader: str) -> None:

        grader_db = f'/home/{grader}/grader.db'

        os.system(f'touch {grader_db}')
        self.chown(grader, grader_db, group=grader)
        self.chmod(644, grader_db)

    def chown(self, user: str, *dirs: Dirs, group: t.Optional[str] = None) -> None:

        who_to = user if not group else ':'.join((user, group))

        os.system(f'chown -R {who_to} {join_dirs(dirs)}')

    def chmod(self, mod: t.Union[str, int], dirs: Dirs) -> None:
        os.system(f'chmod {mod} {join_dirs(dirs)}')

    def enable_nbgrader(self, user: str) -> None:

        logger.debug(f'Enable nbgrader extension for {user}')

        os.system(f"""su {user} -c 'jupyter nbextension install --user --py nbgrader --overwrite \
&& jupyter nbextension enable --user --py nbgrader \
&& jupyter serverextension enable --user --py nbgrader'""")

    def create_user(self, username: str) -> None:

        logger.info(f'Create linux user {username}.')

        os.system(f'adduser -q --gecos "" --disabled-password {username}')

import os
import functools
from pathlib import Path
import typing as t

from loguru import logger

from moodle.typehints import PathLike


Dirs = t.Tuple[PathLike, ...]


def join_dirs(dirs: Dirs) -> str:
    '''
    Concat directories' names.
    Raises TypeError if any of the directory
    in the tuple is not one of str, pathlib.Path or os.PathLike.
    Raises ValueError if dirs is not provided.

        join_dirs([Path('/home/john/'), '/home/john/pictures/'])

        >>> '/home/john/ /home/john/pictures/'

    Args:
        dirs (Dirs): Tuple of PathLike objects.

    Returns:
        str: line of joined directories' names

    '''

    if not dirs:
        raise ValueError('Specify at least one directory to create')

    str_dirs: t.List[str] = []

    for d in dirs:
        if not isinstance(d, (str, Path, os.PathLike)):
            raise TypeError(f'Invalid type of dir {d}: {type(d)}')

        str_dirs.append(str(d))

    return ' '.join(str_dirs)


class SystemCommand:
    '''

    Class for interact with Unix service.

    Used to managing directories, permissions, users and nbgrader extensions.

    '''

    @functools.singledispatchmethod
    def create_dirs(self, *dirs: Dirs) -> None:
        '''
        Create new directories in the system.

        Can be called with unpacked dirs and with iterable as a first argument:

            SystemCommand.create_dirs('dir1', 'dir2')
            SystemCommand.create_dirs(['dir1', 'dir2'])
            SystemCommand.create_dirs(('dir1', 'dir2'))

        Args:
            *dirs (Dirs): Tuple of PathLike objects.

        '''

        # make unrelated directories
        # in contrast with os.mkdirs
        os.system(f'mkdir -p {join_dirs(dirs)}')

        logger.debug(f'Create {len(dirs)} directories: {join_dirs(dirs)}.')

    @create_dirs.register(list)
    @create_dirs.register(tuple)
    def _create_dirs(self, dirs: Dirs): self.create_dirs(*dirs)

    def create_database(self, grader: str) -> None:
        '''
        Create new sqlite database if not exists already.
        Setup permissions to 644 and owner to a grader.

        Args:
            grader (str): Course's grader name

        '''

        grader_db: str = f'/home/{grader}/grader.db'

        os.system(f'touch {grader_db}')
        self.chown(grader, grader_db, group=grader)
        self.chmod(644, grader_db)

    def chown(self, user: str, /, *dirs: Dirs, group: t.Optional[str] = None) -> None:
        '''
        Change owner of files and / or directories in the system.

        Args:
            user (str): New owner's name
            *dirs (Dirs): Tuple of PathLike objects.
            group: Group name. Used if specified. Defaults to None.
        '''

        who_to = user if not group else ':'.join((user, group))

        os.system(f'chown -R {who_to} {join_dirs(dirs)}')

    def chmod(self, mod: t.Union[str, int], *dirs: Dirs) -> None:
        '''
        Update files and / or directories permissions.

        Args:
            mod (t.Union[str, int]): Unix-style permissions.
            *dirs (Dirs): Tuple of PathLike objects.

        '''
        os.system(f'chmod {mod} {join_dirs(dirs)}')

    @staticmethod
    def enable_nbgrader(user: str) -> None:
        '''
        Activate all nbgrader extensions for the user.
        We login as the user and activate all nbgrader extensions for such user.

        Args:
            user (str): User name.

        '''

        logger.debug(f'Enable nbgrader extension for {user}')

        os.system(f"""su {user} -c 'jupyter nbextension install --user --py nbgrader --overwrite \
&& jupyter nbextension enable --user --py nbgrader \
&& jupyter serverextension enable --user --py nbgrader'""")

    @staticmethod
    def create_user(username: str) -> None:
        '''
        Create new user in the system.

        Args:
            username (str): New user's name.
        '''

        logger.info(f'Create linux user {username}.')

        os.system(f'adduser -q --gecos "" --disabled-password {username}')

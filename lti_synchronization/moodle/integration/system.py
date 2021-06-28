import os
import functools
from pathlib import Path
import typing as t

from loguru import logger
from custom_inherit import doc_inherit

from moodle.typehints import Dirs


def join_dirs(dirs: Dirs) -> str:
    '''
    Concat directories' names.

    Examples:

        Pass directories as strings or Path objects::

            join_dirs([Path('/home/john/'), '/home/john/pictures/'])

            >>> '/home/john/ /home/john/pictures/'

    Args:
        dirs (Dirs): tuple of PathLike objects.

    Returns:
        str: string of joined directories' names

    Raises:
        TypeError:
            one item in the dirs is not one of str, pathlib.Path or os.PathLike

    '''

    if not dirs:
        raise ValueError('Specify at least one directory to create')

    str_dirs: t.List[str] = []

    for d in dirs:
        if not isinstance(d, (str, Path, os.PathLike)):
            raise TypeError(f'Invalid type of dir {d}: {type(d)}')
        if not d:
            raise ValueError(f'Empty directory: {d}')

        str_dirs.append(str(d))

    return ' '.join(str_dirs)


@functools.singledispatch
def create_dirs(*dirs) -> None:
    '''
    Create new directories in the system.

    Examples:

        Can be called with unpacked dirs
        and with iterable as first argument::

            SystemCommand.create_dirs('dir1', 'dir2')
            SystemCommand.create_dirs(['dir1', 'dir2'])
            SystemCommand.create_dirs(('dir1', 'dir2'))

    Args:
        *dirs (Dirs): tuple of PathLike objects.

    '''

    # make unrelated directories
    # in contrast with os.mkdirs
    os.system(f'mkdir -p {join_dirs(dirs)}')

    logger.debug(f'Create {len(dirs)} directories: {join_dirs(dirs)}.')


@doc_inherit(create_dirs)
@create_dirs.register(tuple)
@create_dirs.register(list)
def _create_dirs(dirs):
    create_dirs(*dirs)


def create_database(grader: str) -> None:
    '''
    Create new sqlite database if not exists already.
    Setup permissions to 644 and owner to a grader.

    Args:
        grader (str): Course's grader name

    '''

    if grader == '':
        raise ValueError('Grader must be set.')

    grader_db: str = f'/home/{grader}/grader.db'

    os.system(f'touch {grader_db}')

    chown(grader, grader_db, group=grader)

    chmod(644, grader_db)


def chown(user: str, /, *dirs: Dirs, group: t.Optional[str] = None) -> None:
    '''
    Change owner of files and / or directories in the system.

    Args:
        user (str): New owner's name
        *dirs (Dirs): Tuple of PathLike objects.
        group: Group name. Used if specified. Defaults to None.
    '''

    if user == '':
        raise ValueError('User must be set.')

    if group is not None and group == '':
        raise ValueError('Group should not be empty string.')

    who_to = user if not group else ':'.join((user, group))

    os.system(f'chown -R {who_to} {join_dirs(dirs)}')


def chmod(mod: t.Union[str, int], *dirs: Dirs) -> None:
    '''
    Update files and / or directories permissions.

    Args:
        mod (t.Union[str, int]): Unix-style permissions.
        *dirs (Dirs): Tuple of PathLike objects.

    '''

    os.system(f'chmod {mod} {join_dirs(dirs)}')


def enable_nbgrader(user: str) -> None:
    '''
    Activate all nbgrader extensions for the user.
    We login as the user and activate all nbgrader extensions for such user.

    Args:
        user (str): User name.

    '''

    if user == '':
        raise ValueError('User must be set.')

    logger.debug(f'Enable nbgrader extension for {user}')

    os.system(f"su {user} -c 'jupyter nbextension install --user "
              "--py nbgrader --overwrite && jupyter nbextension enable "
              "--user --py nbgrader && jupyter serverextension enable "
              " --user --py nbgrader'")


def create_user(username: str) -> None:
    '''
    Create new user in the system.

    Args:
        username (str): New user's name.
    '''

    logger.info(f'Create linux user {username}.')

    os.system(f'adduser -q --gecos "" --disabled-password {username}')

    chmod(700, f'/home/{username}')

    chown(username, f'/home/{username}')

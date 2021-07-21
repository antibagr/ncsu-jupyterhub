import os
import typing as t

from pathlib import Path


ROLES: t.Tuple[str] = (
    'student',
    'teaching_assistant',
    'teacher',
    'instructional_support',
    'editingteacher',
    'manager',
    'coursecreator'
)

BASE_DIR: Path = Path(__file__).resolve().parent.parent

JSON_FILE: Path = BASE_DIR / 'data' / 'courses.json'

EXCHANGE_DIR: Path = Path('/srv/nbgrader/exchange')

NB_UID = os.environ.get("NB_UID", 10001)
NB_GID = os.environ.get("NB_GID", 100)

DESCRIPTION = r'''
██╗  ████████╗██╗    ███████╗██╗   ██╗███╗   ██╗ ██████╗
██║  ╚══██╔══╝██║    ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝
██║     ██║   ██║    ███████╗ ╚████╔╝ ██╔██╗ ██║██║
██║     ██║   ██║    ╚════██║  ╚██╔╝  ██║╚██╗██║██║
███████╗██║   ██║    ███████║   ██║   ██║ ╚████║╚██████╗
╚══════╝╚═╝   ╚═╝    ╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝

by Anton Bagryanov 2021

LTI Synchronization is a package providing seamless integration to Jupyterhub
and Moodle LMS. It uses Command Line Interface to maintain communication
between two services, but it's also possible to set it up as a cron job.

Read more about cron jobs: https://crontab.guru

Glossary:
* Client  - a part of the program that communicates with Moodle REST API
            and processes raw server response

* Manager - Updates system state using prepared data.

How does it work:

1. The program launches via CLI
2. A Client parses provided arguments with filters, destination folder, etc
3. A Client fetches the data from the Moodle with set up API key
4. A Client processes the data and stores it in memory / JSON file storage.
5. A synchronization manager updates the Jupyterhub configuration file with
   stored data.

To start synchronization between Moodle courses and Jupyterhub services,
provide course filters.
'''

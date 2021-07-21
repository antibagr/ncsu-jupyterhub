'''
LTI Synchronization is a package providing seamless integration to Jupyterhub
and Moodle LMS. It uses Command Line Interface to maintain communication
between two services, but it's also possible to set it up as a cron job.

Read more about cron jobs: https://crontab.guru

Glossary::
    * Client  - a part of the program that communicates with Moodle REST API
                and processes raw server response

    * Manager - Updates system state using prepared data.

How does it work::

    1. The program launches via CLI
    2. A Client parses provided arguments with filters, destination folder, etc
    3. A Client fetches the data from the Moodle with set up API key
    4. A Client processes the data and stores it in memory / JSON file storage.
    5. A synchronization manager updates the Jupyterhub configuration file with
       stored data.

To start synchronization between Moodle courses and Jupyterhub services,
provide course filters.
'''

import sys
import os

try:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(base_dir)
    sys.path.append(os.path.join(base_dir, '..'))
    sys.path.append(os.path.join(base_dir, 'moodle'))

finally:
    from .client.api import MoodleClient
    from .integration.manager import SyncManager
    from .sync import synchronize
    from .authentication.authenticator import LTI13Authenticator

__all__ = [
    'MoodleClient',
    'SyncManager',
    'synchronize',
    'LTI13Authenticator',
]

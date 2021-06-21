'''
...
'''

import sys
import os

base_dir = os.path.abspath(os.path.dirname(__file__))

sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, '..'))
sys.path.append(os.path.join(base_dir, 'moodle'))

from .client.api import MoodleClient
from .integration.manager import SyncManager
from .sync import synchronize
from .authentication.authenticator import LTI13Authenticator


__all__ = ['MoodleClient', 'SyncManager', 'synchronize', 'LTI13Authenticator']

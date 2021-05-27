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

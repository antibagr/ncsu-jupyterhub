import os

from pathlib import Path

from .typehints import PathLike



BASE_DIR: Path = Path(__file__).resolve().parent.parent

EXCHANGE_DIR: Path = Path('/srv/nbgrader/exchange')

NB_UID = os.environ.get("NB_UID", 10001)
NB_GID = os.environ.get("NB_GID", 100)

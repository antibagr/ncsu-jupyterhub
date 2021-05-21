from pathlib import Path

from .typehints import PathLike



BASE_DIR: Path = Path(__file__).resolve().parent.parent

EXCHANGE_DIR: Path = Path('/srv/nbgrader/exchange')

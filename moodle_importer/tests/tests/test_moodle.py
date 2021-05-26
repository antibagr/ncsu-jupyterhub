import typing as t
from unittest.mock import MagicMock, Mock, patch

from moodle.file_gen import FileGenerator


@patch('moodle.file_gen.Gradebook')
@patch('moodle.file_gen.os.system')
def test_moodle(*_mocked_stuff: t.List[MagicMock]):

    gen = FileGenerator()

    with patch('moodle.file_gen.open') as mocked_open:

        gen.generate()

        assert mocked_open

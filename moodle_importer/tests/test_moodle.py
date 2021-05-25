from unittest.mock import patch, Mock

from moodle import FileGenerator


@patch('moodle.file_gen.nbgrader')
def test_moodle():

    gen = FileGenerator()

    gen.generate()

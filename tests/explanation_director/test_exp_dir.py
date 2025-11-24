"""tests for explanation_directory_prototype.exp_dir module."""

from clingo import clingo_main
import pytest
from explanation_directory_prototype.exp_director import ExpDirectorProto
from explanation_directory_prototype.utils import logging
from .test_main import TEST_DIR


class TestExpDir: #pylint: disable=too-few-public-methods
    """Test cases for explanation directory prototype experiment directory functionality."""
    
    
    def test_explanation_director(
        self,
        caplog: pytest.LogCaptureFixture) -> None:
        """Test the ExplanationDirector's `process_files` method on a simple program"""
        caplog.set_level(logging.DEBUG, logger="main")
        file_path = TEST_DIR.joinpath("res/not_a_of_x.lp")
        res = clingo_main(application=ExpDirectorProto(), arguments=[str(file_path.as_posix()), "--outf=3"])
        assert caplog.text  # If no exceptions are raised, the test passes

"""tests for explanation_director_prototype.exp_dir module."""

import re

import pytest
from clingo import clingo_main

from explanation_director_prototype.exp_director import ExpDirectorProto
from explanation_director_prototype.utils import logging

from .test_main import TEST_DIR


class TestExpDir:  # pylint: disable=too-few-public-methods
    """Test cases for explanation director prototype."""

    def test_explanation_director(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the ExplanationDirector's `process_files` method on a simple program"""
        caplog.set_level(logging.DEBUG, logger="main")
        file_path = TEST_DIR.joinpath("res/not_a_of_x.lp")
        res = clingo_main(application=ExpDirectorProto(), arguments=[str(file_path.as_posix()), "--outf=3"])
        assert res == 20  # exit code for search space exhausted
        patterns = [
            r"Minimal core (?:0|1|2):\nCore literals: \[1\]\nExplanation for assumption 1:\n    depends on 1\n",
            r"Minimal core (?:0|1|2):\nCore literals: \[2\]\nExplanation for assumption 2:\n    depends on 2\n",
            r"Minimal core (?:0|1|2):\nCore literals: \[3\]\nExplanation for assumption 3:\n    depends on 3\n",
        ]
        for pattern in patterns:
            assert any(re.search(pattern, msg) for msg in caplog.messages)

"""tests for explanation_director_prototype.exp_dir module."""

import re

import pytest
from clingo import Function, Number, String, Symbol, clingo_main

from explanation_director_prototype.exp_director import ExpDirectorProto
from explanation_director_prototype.utils import logging

from .test_main import TEST_DIR


class TestExpDir:  # pylint: disable=too-few-public-methods
    """Test cases for explanation director prototype."""

    def test_explanation_director(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the ExplanationDirector's `process_files` method on a simple program"""
        caplog.set_level(logging.DEBUG, logger="main")
        file_path = TEST_DIR.joinpath("res/not_a_of_x.lp")
        res = clingo_main(
            application=ExpDirectorProto(), arguments=[str(file_path.as_posix()), "--assumpt-num=3", "--outf=3"]
        )
        assert res == 20  # exit code for search space exhausted
        patterns = [
            (
                r"Minimal core (?:0|1|2):\n"
                r"Core literals: \[1\]\n"
                r"Explanation for assumption 1:\n"
                r"    The programming is failing because of a\(1\).\n"
            ),
            (
                r"Minimal core (?:0|1|2):\n"
                r"Core literals: \[2\]\n"
                r"Explanation for assumption 2:\n"
                r"    The programming is failing because of a\(2\).\n"
            ),
            (
                r"Minimal core (?:0|1|2):\n"
                r"Core literals: \[3\]\n"
                r"Explanation for assumption 3:\n"
                r"    The programming is failing because of a\(3\).\n"
            ),
        ]
        for pattern in patterns:
            assert any(re.search(pattern, msg) for msg in caplog.messages)

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            (
                Function(
                    "_exp",
                    [
                        Function("not_in_same_slot", [], True),
                        Function(
                            "msg",
                            [
                                String("Sessions {} and {} cannot be scheduled without sharing a slot"),
                                Function("", [String("edu"), String("fut")], True),
                            ],
                            True,
                        ),
                    ],
                    True,
                ),
                'Sessions "edu" and "fut" cannot be scheduled without sharing a slot',
            ),
            (
                Function(
                    "_exp",
                    [
                        Function("a_of_x_is_deduced_hence_violating_a_constraint", [], True),
                        Function("msg", [String("exp depends on value of X={}"), Number(3)], True),
                    ],
                    True,
                ),
                "exp depends on value of X=3",
            ),
            (
                Function(
                    "_exp",
                    [
                        Function("rule_violates_integrity", [], True),
                        Function("msg", [String("this rule violates integrity"), Function("", [], True)], True),
                    ],
                    True,
                ),
                "this rule violates integrity",
            ),
        ],
    )
    def test_format_explanation_symbol(self, symbol: Symbol, expected: str) -> None:
        """Test the ExplanationDirector's `format_explanation_symbol` method."""
        director = ExpDirectorProto()
        # Test with a symbol of type Function and name "_exp"
        symbol_explanation = director.format_explanation_symbol(symbol)
        assert symbol_explanation == expected

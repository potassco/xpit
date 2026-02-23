"""Test tag id filters"""

import re

import clingo
import pytest
from clingo.ast import parse_string

from xpit.definitions.define import Argument, TagId, WildCardArgument


@pytest.mark.parametrize(
    "arg1, arg2, expected",
    [
        (Argument(5), Argument(5), True),
        (Argument("a"), Argument(5), False),
        (Argument(lambda x: x < 10), Argument(5), True),
        (Argument(lambda x: "mm" in x), Argument("summer"), True),
        (
            Argument([Argument(lambda x: x % 2 == 0), Argument(lambda x: len(x) <= 4)]),
            Argument([Argument(6), Argument("test")]),
            True,
        ),
        (
            Argument(WildCardArgument("*")),
            Argument([Argument(6), Argument("test")]),
            True,
        ),
        (
            Argument(re.compile("[a-d]{3,3}")),
            Argument("def"),
            False,
        ),
        (
            Argument(re.compile("[a-d]{1,3}")),
            Argument("abc"),
            True,
        ),
    ],
)
def test_argument_allows(arg1: Argument, arg2: Argument, expected: bool) -> None:
    """Test allow method of argument"""
    assert arg1.allows(arg2) is expected, f"arg1= {arg1} allows arg2= {arg2} is not as expected= {expected}"


@pytest.mark.parametrize(
    "arg_other",
    [
        (Argument(lambda x: True)),
    ],
)
def test_allows_exceptions(arg_other: Argument) -> None:
    """Test exceptions in allow method"""
    arg1 = Argument(1)
    with pytest.raises(ValueError, match=r"Other argument must be concrete \(string or integer\) for matching\."):
        arg1.allows(arg_other)


@pytest.mark.parametrize(
    "atom_string, sig_only, expected",
    [
        ("tag(id(1,2,3)).", True, TagId(name="id", arity=3)),
        ("tag(id).", True, TagId(name="id", arity=0)),
        ("tag(id2(1)).", True, TagId(name="id2", arity=1)),
        (
            """tag(id(1,"asdf",asd,X,(1,zwei))).""",
            False,
            TagId(
                name="id",
                arity=5,
                arguments=[
                    Argument(1),
                    Argument("asdf"),
                    Argument("asd"),
                    Argument(WildCardArgument("*")),
                    Argument([Argument(1), Argument("zwei")]),
                ],
            ),
        ),
    ],
)
def test_tag_id_init_from_ast(atom_string: str, sig_only: bool, expected: list[Argument]) -> None:
    """test tag id init"""
    ast_list: list[clingo.ast.AST] = []
    parse_string(atom_string, ast_list.append)
    assert TagId.from_ast(ast_list[1].head.atom.symbol.arguments[0], sig_only=sig_only) == expected

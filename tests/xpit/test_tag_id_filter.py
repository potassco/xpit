"""Test tag id filters"""

import re

import clingo
import pytest
from clingo.ast import parse_string

from xpit.definitions.define import Argument, PortionId, PortionIdFilter, WildCardArgument


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
            Argument([Argument(lambda x: x % 2 == 0), Argument(lambda x: len(x) <= 4)]),
            Argument([Argument(6)]),
            False,
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
    "id_, arity, input_args, expected",
    [
        [
            "r1",
            3,
            [Argument(4), "string", WildCardArgument("*")],
            PortionId("r1", 3, [Argument(4), Argument("string"), Argument(WildCardArgument("*"))]),
        ],
    ],
)
def test_tagid_init(id_: str, arity: int, input_args: list[Argument], expected: PortionId) -> None:
    """test init method of tagid"""
    assert expected.allows(PortionId(id_, arity, input_args))


@pytest.mark.parametrize(
    "tag_str, expected",
    [
        ("r1/2", PortionId("r1", 2)),
        ("r2", PortionId("r2")),
    ],
)
def test_tag_id_init_from_str(tag_str: str, expected: PortionId) -> None:
    """test tag id init from str"""
    tag_id = PortionId.from_str(tag_str)
    assert expected.allows(tag_id)
    assert tag_id.allows(expected)


@pytest.mark.parametrize(
    "tag_id, expected",
    [
        [PortionId("r1", 3, [Argument(4), Argument("string"), Argument(WildCardArgument("*"))]), "r1/3"],
        [PortionId("r1", 1, [[Argument(4), Argument("string"), Argument(WildCardArgument("*"))]]), "r1/1"],
        [PortionId("r1"), "r1/*"],
        [PortionId("r1", 0), "r1"],
    ],
)
def test_repr_tagid(tag_id: PortionId, expected: str) -> None:
    """test representation of tag_id"""
    assert repr(tag_id) == expected


@pytest.mark.parametrize(
    "atom_string, sig_only, expected",
    [
        ("tag(id(1,2,3)).", True, PortionId(name="id", arity=3)),
        ("tag(id).", True, PortionId(name="id", arity=0)),
        ("tag(id2(1)).", True, PortionId(name="id2", arity=1)),
        (
            """tag(id(1,"asdf",asd,X,(1,zwei))).""",
            False,
            PortionId(
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
        ("""tag("id").""", True, PortionId(name="id", arity=0)),
    ],
)
def test_tag_id_init_from_ast(atom_string: str, sig_only: bool, expected: PortionId) -> None:
    """test tag id init"""
    ast_list: list[clingo.ast.AST] = []
    parse_string(atom_string, ast_list.append)
    assert expected.allows(PortionId.from_ast(ast_list[1].head.atom.symbol.arguments[0], sig_only=sig_only))


@pytest.mark.parametrize(
    "clingo_symbol, expected",
    [
        (clingo.Function("r1", [clingo.String("b")], True), PortionId("r1", 1, ["b"])),
        (clingo.Function("r1", [clingo.Number(1)], True), PortionId("r1", 1, [1])),
        (clingo.Function("r1", [clingo.String("b"), clingo.Number(1)], True), PortionId("r1", 2, ["b", 1])),
        (clingo.String("b"), PortionId("b", 0)),
        (
            clingo.Function("r1", [clingo.Function("", [clingo.Number(1), clingo.Number(2)], True)], True),
            PortionId("r1", 1, [Argument([Argument(1), Argument(2)])]),
        ),
    ],
)
def test_tag_id_init_from_clingo_symbol(clingo_symbol: clingo.symbol.Symbol, expected: PortionId) -> None:
    """test creation of TagId from clingo_symbol"""
    tag_id = PortionId.from_clingo_symbol(clingo_symbol)
    assert expected.allows(tag_id)
    assert tag_id.allows(expected)


@pytest.mark.parametrize(
    "tag_id_filter, tag_id, allows",
    [
        (PortionIdFilter([]), PortionId("tag2", 2), [PortionId("tag2", 2, [1, 2])]),
        (PortionIdFilter([]), "tag2/2", [PortionId("tag2", 2, ["abc", "def"])]),
        (PortionIdFilter([]), "tag2", [PortionId("tag2", 2, ["abc", "def"]), PortionId("tag2", 1, ["def"])]),
    ],
)
def test_tag_id_filter_append(tag_id_filter: PortionIdFilter, tag_id: PortionId | str, allows: list[PortionId]) -> None:
    """test append method of tag_id_filter"""
    tag_id_filter.append(tag_id)
    assert all(tag_id_filter.allows(test_tag_id) for test_tag_id in allows)

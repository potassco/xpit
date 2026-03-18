"""Test tag id filters"""

from typing import Sequence

import clingo
import pytest
from clingo.ast import parse_string

from xpit.definitions.define import Argument, PortionId, PortionIdFilter, WildCardArgument


@pytest.mark.parametrize(
    "ast, expected",
    [
        ("tag(id(f(1))).", Argument(("id", [Argument(("f", [Argument(1)]))]))),
        ("tag(id).", Argument("id")),
        ("tag(1).", Argument(1)),
        ('tag("id").', Argument("id")),
        ("tag(id()).", Argument(("id", []))),
        ("tag(id).", Argument("id")),
        ("tag(id((1,2,3))).", Argument(("id", [Argument([Argument(1), Argument(2), Argument(3)])]))),
    ],
)
def test_argument_from_ast(ast: str, expected: Argument) -> None:
    """test creation of Argument from ast"""
    ast_list: list[clingo.ast.AST] = []
    parse_string(ast, ast_list.append)
    argument = Argument.from_ast(ast_list[1].head.atom.symbol.arguments[0])
    assert expected.allows(argument)
    assert argument.allows(expected)


@pytest.mark.parametrize(
    "symbol, expected",
    [
        (clingo.Number(1), Argument(1)),
        (clingo.String("id"), Argument("id")),
        (clingo.Function("id", [], True), Argument("id")),
        (clingo.Function("id", [clingo.Number(1)], True), Argument(("id", [Argument(1)]))),
        (
            clingo.Function("id", [clingo.String("a"), clingo.Number(2)], True),
            Argument(("id", [Argument("a"), Argument(2)])),
        ),
        (
            clingo.Function("id", [clingo.Function("f", [clingo.Number(1)], True)], True),
            Argument(("id", [Argument(("f", [Argument(1)]))])),
        ),
        (
            clingo.Function(
                "id", [clingo.Function("f", [clingo.Number(1), clingo.String("b")], True), clingo.Number(2)], True
            ),
            Argument(("id", [Argument(("f", [Argument(1), Argument("b")])), Argument(2)])),
        ),
        (clingo.Function("", [clingo.Number(1), clingo.Number(2)], True), Argument([Argument(1), Argument(2)])),
    ],
)
def test_argument_from_clingo_symbol(symbol: clingo.symbol.Symbol, expected: Argument) -> None:
    """test creation of Argument from clingo symbol"""
    argument = Argument.from_clingo_symbol(symbol)
    assert expected.allows(argument)
    assert argument.allows(expected)


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
        [PortionId("r1", 3, [Argument(4), Argument("string"), Argument(WildCardArgument("*"))]), "r1(4, string, *)"],
        [
            PortionId("r1", 1, [[Argument(4), Argument("string"), Argument(WildCardArgument("*"))]]),
            "r1((4, string, *))",
        ],
        [PortionId("r1"), "r1/*"],
        [PortionId("r1", 0), "r1"],
        [PortionId("r1", 0), "r1"],
        [PortionId("r1", 2), "r1/2"],
    ],
)
def test_repr_tagid(tag_id: PortionId, expected: str) -> None:
    """test representation of tag_id"""
    assert repr(tag_id) == expected


def test_repr_argument_lambda_in_argument() -> None:
    """test representation of lambda in argument"""
    arg = Argument(lambda x: x < 10)
    arg_repr = repr(arg)
    print(arg_repr)
    assert arg_repr.startswith("<callable <function test_repr_argument_lambda_in_argument.<locals>.<lambda> at ")
    assert arg_repr.endswith(">>")


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
        (clingo.Function("r1", [], True), PortionId("r1", 0, [])),
        (
            clingo.Function("fact", [clingo.Function("b", [], True), clingo.Number(1)], True),
            PortionId("fact", 2, [Argument("b"), Argument(1)]),
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


@pytest.mark.parametrize(
    "portion_id_filter, portion_ids",
    [
        (
            PortionIdFilter([PortionId("tag2", 2)]),
            [PortionId("tag2", 2, [1, 2]), PortionId("tag2", 3, ["abc", "def", "ghi"])],
        ),
        (PortionIdFilter([PortionId("tag2", 2)]), [PortionId("tag2", 2, ["abc", "def"])]),
        (PortionIdFilter([PortionId("tag2")]), [PortionId("tag2", 3, ["abc", "def", "ghi"])]),
    ],
)
def test_portion_id_filter_extend(portion_id_filter: PortionIdFilter, portion_ids: Sequence[PortionId]) -> None:
    """test extend method of tag_id_filter"""
    portion_id_filter.extend(portion_ids)
    for portion_id in portion_ids:
        assert (
            portion_id in portion_id_filter.tags
        ), f"PortionId {portion_id} should be in the filter after extend, but is not. Filter: {portion_id_filter.tags}"

"""test functionalities of ProgramExplainer in integration with Director"""

from typing import Callable

import clingo
import pytest
from clingo.ast import parse_string

from tests.xpit.test_main import TEST_DIR
from xpit.director.director import ExplanationDirector
from xpit.explainer.program import ExplainablePortionTransformer, ProgramExplainer

from ..utils import fixture_director_factory  # pylint: disable=unused-import


class MockBuilder:
    """Class mocking a clingo builder for testing purposes."""

    def __init__(self, control=None) -> None:  # type: ignore
        """initializes the mock builder."""
        self.control = control

    def add(self, *args, **kwargs) -> None:  # type: ignore
        """mock add method."""
        # Does nothing, just a placeholder for the real method


def test_add_lp_files(director_factory: Callable[[int], ExplanationDirector]) -> None:
    """Test adding LP files to ProgramExplainer."""

    director_factory(10)
    explainer = ProgramExplainer()
    assert not explainer.lp_files, "Initial lp_files should be empty."
    lp_files = ["test1.lp", "test2.lp"]
    for file in lp_files:
        explainer.add_lp_file(file)
        assert file in explainer.lp_files, f"LP file {file} should be added to explainer."
    assert len(explainer.lp_files) == len(lp_files), "Number of lp_files should match the number of added files."


def test_add_lp_strings(director_factory: Callable[[int], ExplanationDirector]) -> None:
    """Test adding LP strings to ProgramExplainer."""

    director_factory(10)
    explainer = ProgramExplainer(lp_files=[], lp_strings=[])
    assert not explainer.lp_strings, "Initial lp_strings should be empty."
    lp_strings = ["a :- b.", "c :- d."]
    for lp_string in lp_strings:
        explainer.add_lp_string(lp_string)
        assert lp_string in explainer.lp_strings, f"LP string '{lp_string}' should be added to explainer."
    assert len(explainer.lp_strings) == len(
        lp_strings
    ), "Number of lp_strings should match the number of added strings."


@pytest.mark.parametrize(
    "file, expected_ids, duplicate_warning",
    [
        ("not_a_of_x.lp", ["r1"], False),
        ("dupl_ids.lp", ["r1"], True),
    ],
)
def test_setup_before_grounding(
    caplog: pytest.LogCaptureFixture,
    director_factory: Callable[[int], "ExplanationDirector"],
    file: str,
    expected_ids: list[str],
    duplicate_warning: bool,
) -> None:
    """test setup_before_grounding of ProgramExplainer."""
    file_path = TEST_DIR.joinpath(f"res/{file}")
    explainer = ProgramExplainer(lp_files=[str(file_path)])
    director = director_factory(5)
    director.register_explainer(explainer)
    with caplog.at_level("WARNING"):
        director.setup_before_grounding()
    # pylint: disable=protected-access
    assert len(explainer._exp_portion_ids) == len(expected_ids), "There should be 1 explainable portion identified."
    assert all(rid in explainer._exp_portion_ids for rid in expected_ids), "Expected explainable portion id not found."
    if duplicate_warning:
        assert "Duplicate explainable portion id found" in caplog.text


@pytest.mark.parametrize(
    "num_eunits, file, expected_binding_size_of_last_eunit",
    [
        (3, "not_a_of_x.lp", 1),
        (2, "not_a_of_x.lp", 2),
        (4, "not_a_of_x.lp", 0),
    ],
)
def test_assign_eunit_budget(
    director_factory: Callable[[int], ExplanationDirector],
    num_eunits: int,
    file: str,
    expected_binding_size_of_last_eunit: int,
) -> None:
    """test assign_eunit_budget of ProgramExplainer."""
    director = director_factory(num_eunits)
    file_path = TEST_DIR.joinpath(f"res/{file}")
    explainer = ProgramExplainer(lp_files=[str(file_path)])
    director.register_explainer(explainer)
    director.setup_before_grounding()
    director.control.ground([("base", [])])
    director.setup_before_solving()

    assert len(explainer.get_explainable_portions(director.eunits[-1])) == expected_binding_size_of_last_eunit
    if expected_binding_size_of_last_eunit > 0:
        # pylint: disable=protected-access
        assert len(explainer._binding.keys()) == num_eunits, "All eunits should have bindings."


@pytest.mark.parametrize(
    "rule_str, exp_rule_str, is_marked_for_explanation",
    [
        ("a :- b, not _explain(r1, msg()).", "a :- b, not _exp(r1, msg()). {_exp(r1, msg())} :- b.", True),
        ("c :- d.", "c :- d.", False),
    ],
)
def test_transform_rule(
    caplog: pytest.LogCaptureFixture, rule_str: str, exp_rule_str: str, is_marked_for_explanation: bool
) -> None:
    """test _transform_rule of ExplainablePortionTransformer."""
    ast_nodes: list[clingo.ast.AST] = []
    parse_string(rule_str, ast_nodes.append)
    ast = ast_nodes[1]
    transformer = ExplainablePortionTransformer(builder=MockBuilder())  # type: ignore
    with caplog.at_level("DEBUG"):
        t_asts = list(transformer._transform_rule(ast))  # pylint: disable=protected-access

    expected_ast_nodes: list[clingo.ast.AST] = []
    parse_string(exp_rule_str, expected_ast_nodes.append)

    assert all(t_ast in expected_ast_nodes for t_ast in t_asts), "Transformed ASTs should match expected ASTs."
    if is_marked_for_explanation:
        assert "marked for explanation" in caplog.text
        assert "New rule added" in caplog.text
    else:
        assert "marked for explanation" not in caplog.text
        assert "New rule added" not in caplog.text


@pytest.mark.parametrize(
    "lp_strings, expected_request",
    [
        (['a :- not _explain(r1, msg("",())). :- a.'], 1),
        (['b(X) :- X=1..5, not _explain(r2, msg("",(X))). :- b(X).'], 5),
        (["c :- d."], 0),
    ],
)
def test_get_eunit_request(
    lp_strings: list[str],
    expected_request: int,
) -> None:
    """test get_eunit_request of ProgramExplainer."""
    explainer = ProgramExplainer(lp_strings=lp_strings)
    ctl = clingo.Control()
    explainer.set_control(ctl)
    explainer.setup_before_grounding()
    ctl.ground([("base", [])])
    request = explainer.get_eunit_request()
    assert request == expected_request, f"EUnit request should be {expected_request}."

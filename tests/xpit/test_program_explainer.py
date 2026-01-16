"""test functionalities of ProgramExplainer in integration with Director"""

from typing import Callable

import pytest
from clingo.ast import parse_string

from tests.xpit.test_main import TEST_DIR
from xpit.director.director import ExplanationDirector
from xpit.explainer import program as program_module
from xpit.explainer.program import ExplainablePortionTransformer, ProgramExplainer

from ..utils import director_factory


class MockBuilder:

    def __init__(self, control=None):
        self.control = control

    def add(self, *args, **kwargs):
        pass  # Does nothing, just a placeholder for the real method


def test_add_lp_files(director_factory):

    director_factory(10)
    explainer = ProgramExplainer(lp_files=[])
    assert explainer.lp_files == [], "Initial lp_files should be empty."
    lp_files = ["test1.lp", "test2.lp"]
    for file in lp_files:
        explainer.add_lp_file(file)
        assert file in explainer.lp_files, f"LP file {file} should be added to explainer."
    assert len(explainer.lp_files) == len(lp_files), "Number of lp_files should match the number of added files."


@pytest.mark.parametrize(
    "file, expected_ids, duplicate_warning",
    [
        ("not_a_of_x.lp", ["r1"], False),
        ("dupl_ids.lp", ["r1"], True),
    ],
)
def test_setup_before_rounding(
    caplog,
    director_factory: Callable[[int], "ExplanationDirector"],
    file: str,
    expected_ids: list[str],
    duplicate_warning: bool,
):

    file_path = TEST_DIR.joinpath(f"res/{file}")
    explainer = ProgramExplainer(lp_files=[str(file_path)])
    director = director_factory(5)
    director.register_explainer(explainer)
    with caplog.at_level("WARNING"):
        director.setup_before_grounding()
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
def test_assign_eunit_budget(director_factory, num_eunits: int, file: str, expected_binding_size_of_last_eunit: int):

    director = director_factory(num_eunits)
    file_path = TEST_DIR.joinpath(f"res/{file}")
    explainer = ProgramExplainer(lp_files=[str(file_path)])
    director.register_explainer(explainer)
    director.setup_before_grounding()
    director.control.ground([("base", [])])
    director.setup_before_solving()

    assert len(explainer.get_explainable_portions(director.eunits[-1])) == expected_binding_size_of_last_eunit
    if expected_binding_size_of_last_eunit > 0:
        assert len(explainer._binding.keys()) == num_eunits, "All eunits should have bindings."


@pytest.mark.parametrize(
    "rule_str, exp_rule_str, is_marked_for_explanation",
    [
        ("a :- b, not _explain(r1, msg()).", "a :- b, not _exp(r1, msg()). {_exp(r1, msg())} :- b.", True),
        ("c :- d.", "c :- d.", False),
    ],
)
def test_transform_rule(caplog, rule_str, exp_rule_str, is_marked_for_explanation):

    ast_nodes = []
    parse_string(rule_str, lambda stm: ast_nodes.append(stm))
    ast = ast_nodes[1]
    transformer = ExplainablePortionTransformer(builder=MockBuilder())
    with caplog.at_level("DEBUG"):
        t_asts = list(transformer._transform_rule(ast))

    expected_ast_nodes = []
    parse_string(exp_rule_str, lambda stm: expected_ast_nodes.append(stm))

    assert all(t_ast in expected_ast_nodes for t_ast in t_asts), "Transformed ASTs should match expected ASTs."
    if is_marked_for_explanation:
        assert "marked for explanation" in caplog.text
        assert "New rule added" in caplog.text
    else:
        assert "marked for explanation" not in caplog.text
        assert "New rule added" not in caplog.text

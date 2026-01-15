"""test functionalities of ProgramExplainer in integration with Director"""

import pytest
from clingo.ast import parse_string

from xpit.explainer.program import ExplainablePortionTransformer

from ..utils import director_factory, explainer_factory


def test_add_lp_files(director_factory, explainer_factory):

    director = director_factory(10)
    explainer = explainer_factory(director=director, type_="program", lp_files=[])
    assert explainer.lp_files == [], "Initial lp_files should be empty."
    lp_files = ["test1.lp", "test2.lp"]
    for file in lp_files:
        explainer.add_lp_file(file)
        assert file in explainer.lp_files, f"LP file {file} should be added to explainer."
    assert len(explainer.lp_files) == len(lp_files), "Number of lp_files should match the number of added files."


class MockBuilder:
    def add(self, *args, **kwargs):
        pass  # Does nothing, just a placeholder for the real method


@pytest.mark.parametrize(
    "rule_str, exp_rule_str1, exp_rule_str2, is_marked_for_explanation",
    [
        ("a :- b, not _explain(1).", "a :- b, not _exp(1).", "{_exp(1)} :- b.", True),
        ("c :- d.", "c :- d.", "", False),
    ],
)
def test_visit_rule(caplog, rule_str, exp_rule_str1, exp_rule_str2, is_marked_for_explanation):

    ast_nodes = []
    parse_string(rule_str, lambda stm: ast_nodes.append(stm))
    ast = ast_nodes[1]
    transformer = ExplainablePortionTransformer(builder=MockBuilder())
    with caplog.at_level("DEBUG"):
        transformed_ast = transformer.visit_Rule(ast)

    expected_ast_nodes = []
    parse_string(exp_rule_str1, lambda stm: expected_ast_nodes.append(stm))
    expected_ast = expected_ast_nodes[1]

    if is_marked_for_explanation:
        ast_rule_in_log_nodes = []
        parse_string(exp_rule_str2, lambda stm: ast_rule_in_log_nodes.append(stm))
        ast_rule_in_log = ast_rule_in_log_nodes[1]

    assert transformed_ast == expected_ast, "The transformed AST should match the expected AST."
    if is_marked_for_explanation:
        assert "marked for explanation" in caplog.text
        assert "New rule added" in caplog.text
        assert str(ast_rule_in_log) in caplog.text
    else:
        assert "marked for explanation" not in caplog.text
        assert "New rule added" not in caplog.text

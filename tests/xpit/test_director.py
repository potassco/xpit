"""tests for explanation_director_prototype.exp_dir module."""

import clingo
import pytest
from clingo import Function, Number, String, Symbol, clingo_main

from xpit.definitions.define import ExplanationUnit
from xpit.director.director import ExplanationDirector
from xpit.explainer.program import ProgramExplainer
from xpit.utils import logging

from .test_main import TEST_DIR


def test_register_explainer(director_factory, explainer_factory):
    """Test registering an explainer."""

    director = director_factory(2)
    assert len(director.explainers) == 0, "Explainers list should be empty initially."

    # create ProgramExplainer instance
    explainer1 = explainer_factory(director=director, type_="program", lp_files=[])
    explainer2 = explainer_factory(director=director, type_="program", lp_files=[])
    explainer3 = explainer_factory(director=director, type_="program", lp_files=[])

    director.register_explainer(explainer1)
    assert explainer1 in director.explainers, "Explainer should be registered in the director."
    assert len(director.explainers) == 1, "Explainers list should have just one explainer."
    director.register_explainer(explainer2)
    assert explainer2 in director.explainers, "Second explainer should be registered in the director."
    assert len(director.explainers) == 2, "Explainers list should have two explainers."
    with pytest.raises(ValueError, match="Number of registered explainers exceeds maximum number of eunits."):
        director.register_explainer(explainer3)  # Exceeds maximum_number_of_eunits


def test_find_eunit_for_assumption_literal(director_factory):
    """Test finding eunit for a given assumption literal."""

    director_factory(5)
    pass  # further implementation would be needed here to create eunits and test the method


@pytest.mark.parametrize(
    "num_eunits",
    [
        4,
        5,
        10,
    ],
)
def test_create_eunits(director_factory, num_eunits):
    """Test creation of explanation units (eunits)."""

    director = director_factory(num_eunits)
    director._create_eunits()
    assert len(director.eunits) == num_eunits, "Number of created eunits should match the specified number."
    assert isinstance(director.eunits[0], ExplanationUnit), "Created objects should be instances of ExplanationUnit."
    # TODO: can we test that smth was added to backend?


@pytest.mark.parametrize(
    "num_eunits",
    "num_explainers",
    "distribution"[
        (4, 2, [2, 2]),
        (5, 2, [3, 2]),
        (10, 3, [4, 3, 3]),
        (200, 7, [29, 29, 29, 29, 28, 28, 28]),
    ],
)
def test_distribute_eunits_equally(director_factory, explainer_factory, num_eunits, num_explainers, distribution):
    """Test equal distribution of eunits among explainers."""

    director = director_factory(num_eunits)

    # Register multiple explainers
    for _ in range(num_explainers):
        explainer = explainer_factory(director=director, type_="program", lp_files=[])
        director.register_explainer(explainer)

    distribution = director._distribute_eunits_equally()

    assert sum(distribution) == num_eunits, "Total distributed eunits should equal the maximum number."
    assert len(distribution) == num_explainers, "Distribution list length should match number of explainers."
    assert distribution == distribution, "Distribution should match expected distribution."


def test_setup_before_solving(director_factory):  # TODO: what should be tested here?
    """Test setup before solving, including eunit creation and distribution."""

    num_eunits = 6
    director = director_factory(num_eunits)

    # Register multiple explainers
    for _ in range(2):
        explainer = ProgramExplainer(director=director, lp_files=[])
        director.register_explainer(explainer)

    director.setup_before_solving()

    assert len(director.eunits) == num_eunits, "Number of created eunits should match the maximum number."

    distribution = director._distribute_eunits_equally()
    assert sum(distribution) == num_eunits, "Total distributed eunits should equal the maximum number."


def test_compute_minimal_core_eunits(director_factory):  # TODO: a little bit more difficult to test?
    """Test computation of minimal core eunits."""

    director = director_factory(5)

    # Register an explainer
    explainer = ProgramExplainer(director=director, lp_files=[])
    director.register_explainer(explainer)

    director.setup_before_solving()

    list(director.compute_minimal_core_eunits())

    pass  # further implementation would be needed here to validate the minimal cores


def test_compute_explanation(director_factory):
    """Test computation of explanations from a core of eunits."""

    director = director_factory(5)

    # Register an explainer
    explainer = ProgramExplainer(director=director, lp_files=[])
    director.register_explainer(explainer)

    director.setup_before_solving()

    # Create a mock core of eunits
    core_eunits = director.eunits[:3]  # take first 3 eunits as core

    director.compute_explanation(core_eunits)

    pass  # further implementation would be needed here to validate the explanation

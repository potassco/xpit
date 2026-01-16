"""tests for explanation_director_prototype.exp_dir module."""

import clingo
import pytest
from clingo import Function, Number, String, Symbol, clingo_main

from xpit.definitions.define import ExplanationUnit
from xpit.director.director import ExplanationDirector
from xpit.explainer.program import ProgramExplainer
from xpit.utils import logging

from ..utils import director_factory
from .test_main import TEST_DIR


def test_register_explainer(director_factory):
    """Test registering an explainer."""

    director = director_factory(2)
    assert len(director.explainers) == 0, "Explainers list should be empty initially."

    # create ProgramExplainer instance
    explainer1 = ProgramExplainer(lp_files=[])
    explainer2 = ProgramExplainer(lp_files=[])
    explainer3 = ProgramExplainer(lp_files=[])

    director.register_explainer(explainer1)
    assert explainer1 in director.explainers, "Explainer should be registered in the director."
    assert len(director.explainers) == 1, "Explainers list should have just one explainer."
    director.register_explainer(explainer2)
    assert explainer2 in director.explainers, "Second explainer should be registered in the director."
    assert len(director.explainers) == 2, "Explainers list should have two explainers."
    with pytest.raises(ValueError, match="Number of registered explainers exceeds maximum number of eunits."):
        director.register_explainer(explainer3)  # Exceeds maximum_number_of_eunits


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


@pytest.mark.parametrize(
    "num_eunits, num_explainers, distribution",
    [
        (4, 2, [2, 2]),
        (5, 2, [3, 2]),
        (10, 3, [4, 3, 3]),
        (200, 7, [29, 29, 29, 29, 28, 28, 28]),
    ],
)
def test_distribute_eunits_equally(director_factory, num_eunits, num_explainers, distribution):
    """Test equal distribution of eunits among explainers."""

    director = director_factory(num_eunits)

    # Register multiple explainers
    for _ in range(num_explainers):
        explainer = ProgramExplainer(lp_files=[])
        director.register_explainer(explainer)

    distribution = director._distribute_eunits_equally()

    assert sum(distribution) == num_eunits, "Total distributed eunits should equal the maximum number."
    assert len(distribution) == num_explainers, "Distribution list length should match number of explainers."
    assert distribution == distribution, "Distribution should match expected distribution."


@pytest.mark.parametrize(
    "num_eunit, file, num_cores, ids_in_cores",
    [
        (3, "not_a_of_x.lp", 3, [{"r1"}]),
        (2, "not_a_of_x.lp", 2, [{"r1"}]),
        (4, "not_a_of_x.lp", 3, [{"r1"}]),
        (2, "ex1.lp", 1, [{"r1"}]),
        (1, "ex1.lp", 1, [{"r1"}]),
        (2, "ex2.lp", 1, [{"r1"}]),
        (1, "ex2.lp", 1, [{}]),
    ],
)
def test_director(director_factory, num_eunit, file, num_cores, ids_in_cores):

    director = director_factory(num_eunit)
    explainer = ProgramExplainer(lp_files=[str(TEST_DIR.joinpath(f"res/{file}"))])
    director.register_explainer(explainer)
    director.setup_before_grounding()
    director.control.ground([("base", [])])
    director.setup_before_solving()

    cores = list(director.compute_minimal_core_eunits())
    assert len(cores) == num_cores
    for core in cores:
        exp_portions = director.compute_explanation(core)
        assert set(ep.id_ for ep in exp_portions) in ids_in_cores

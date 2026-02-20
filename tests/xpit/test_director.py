"""tests for xpit module."""

from typing import Callable

import clingo
import pytest

from xpit.definitions.define import ExplanationUnit, TagId
from xpit.director.director import ExplanationDirector
from xpit.explainer.program import ProgramExplainer

from ..utils import fixture_director_factory  # pylint: disable=unused-import
from .test_main import TEST_DIR


@pytest.mark.parametrize(
    "enum_num",
    [
        1,
        5,
        -3,
        0,
    ],
)
def test_init(enum_num: int) -> None:
    """Test initialization of ExplanationDirector."""

    ctl = clingo.Control()

    if enum_num < 1:
        with pytest.raises(ValueError, match="Maximum number of eunits must be at least 1."):
            ExplanationDirector(ctl, enum_num)
    else:
        director = ExplanationDirector(ctl, enum_num)
        assert director.control == ctl, "Control object should be set correctly."
        assert director.maximum_number_of_eunits == enum_num, "Maximum number of eunits should be set correctly."
        assert not director.explainers, "Explainers list should be initialized as empty."
        assert not director.eunits, "Eunits list should be initialized as empty."


def test_register_explainer(director_factory: Callable[[int], ExplanationDirector]) -> None:
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
def test_create_eunits(director_factory: Callable[[int], ExplanationDirector], num_eunits: int) -> None:
    """Test creation of explanation units (eunits)."""

    director = director_factory(num_eunits)
    director._create_eunits()  # pylint: disable=protected-access
    assert len(director.eunits) == num_eunits, "Number of created eunits should match the specified number."
    assert isinstance(director.eunits[0], ExplanationUnit), "Created objects should be instances of ExplanationUnit."


@pytest.mark.parametrize(
    "num_eunits, num_explainers, expected_distribution",
    [
        (4, 2, [2, 2]),
        (5, 2, [3, 2]),
        (10, 3, [4, 3, 3]),
        (200, 7, [29, 29, 29, 29, 28, 28, 28]),
    ],
)
def test_distribute_eunits_equally(
    director_factory: Callable[[int], ExplanationDirector],
    num_eunits: int,
    num_explainers: int,
    expected_distribution: list[int],
) -> None:
    """Test equal distribution of eunits among explainers."""

    director = director_factory(num_eunits)

    # Register multiple explainers
    for _ in range(num_explainers):
        explainer = ProgramExplainer(lp_files=[])
        director.register_explainer(explainer)

    distribution = director._distribute_eunits_equally()  # pylint: disable=protected-access

    assert sum(distribution) == num_eunits, "Total distributed eunits should equal the maximum number."
    assert len(distribution) == num_explainers, "Distribution list length should match number of explainers."
    assert expected_distribution == distribution, "Distribution should match expected distribution."


@pytest.mark.parametrize(
    "lp_strings_per_explainer, num_eunits, expected_distribution",
    [
        ([["d."], ['a(X) :- X=1..10, not _explain(r1,("",(X))). :- a(X).']], 2, [1, 1]),
        ([["d."], ['a(X) :- X=1..10, not _explain(r1,("",())). :- a(X).']], 8, [0, 1]),
        ([["d."], ['a(X) :- X=1..10, not _explain(r1,("",(X))). :- a(X).']], 8, [1, 7]),
        (
            [
                ['b(X) :- X=1..5, not _explain(r1,("",(X))). :- b(X).'],
                ['a(X) :- X=1..10, not _explain(r2,("",(X))). :- a(X).'],
            ],
            3,
            [1, 2],
        ),
        ([['b(X) :- X=1..5, not _explain(r1,("",(X))). :- b(X).']], 2, [2]),
        ([['b(X) :- X=1..5, not _explain(r1,("",())). :- b(X).']], 2, [1]),
        (
            [
                ['b(X) :- X=1..5, not _explain(b1,("",(X))). :- b(X), c(X), d(X).'],
                ['c(X) :- X=1..5, not _explain(c1,("",(X))).'],
                ['d(X) :- X=1..5, not _explain(d1,("",(X))).'],
            ],
            4,
            [2, 1, 1],
        ),
    ],
)
def test_distribute_eunits_by_request(
    lp_strings_per_explainer: list[list[str]],
    num_eunits: int,
    expected_distribution: list[int],
    director_factory: Callable[[int], ExplanationDirector],
) -> None:
    """Test distribution of eunits by request."""

    director = director_factory(num_eunits)

    # Register multiple explainers with given LP strings
    for lp_strings in lp_strings_per_explainer:
        explainer = ProgramExplainer(lp_files=[], lp_strings=lp_strings)
        director.register_explainer(explainer)

    director.setup_before_grounding()
    director.control.ground([("base", [])])

    distribution = director._distribute_eunits_by_request()  # pylint: disable=protected-access

    assert len(distribution) == len(
        expected_distribution
    ), "Distribution list length should match number of explainers."
    assert expected_distribution == distribution, "Distribution should match expected distribution."


@pytest.mark.parametrize(
    "num_eunit, file, prog_str, num_cores, ids_in_cores",
    [
        (3, "not_a_of_x.lp", "", 3, [{TagId("r1", 0, [])}]),
        (2, "not_a_of_x.lp", "", 2, [{TagId("r1", 0, [])}]),
        (4, "not_a_of_x.lp", "", 3, [{TagId("r1", 0, [])}]),
        (2, "ex1.lp", "", 1, [{TagId("r1", 0, [])}]),
        (1, "ex1.lp", "", 1, [{TagId("r1", 0, [])}]),
        (2, "ex2.lp", "", 1, [{TagId("r1", 0, [])}]),
        (1, "ex2.lp", "", 0, []),  # this might be a bug in cling-explaid; does not work with ASP-explorer.
        (3, "sat1.lp", "", 0, []),
        (1, "", 'a :- not _explain(r1, msg("",())). :-a. ', 1, [{TagId("r1", 0, [])}]),
    ],
)
def test_director(  # pylint: disable=too-many-positional-arguments
    director_factory: Callable[[int], ExplanationDirector],
    num_eunit: int,
    file: str,
    prog_str: str,
    num_cores: int,
    ids_in_cores: list[set[str]],
) -> None:
    """test ExplanationDirector usage."""

    director = director_factory(num_eunit)
    explainer = ProgramExplainer(
        lp_files=[str(TEST_DIR.joinpath(f"res/{file}"))] if file else [], lp_strings=[prog_str] if prog_str else []
    )
    director.register_explainer(explainer)
    director.setup_before_grounding()
    director.control.ground([("base", [])])
    director.setup_before_solving()

    cores = list(director.compute_minimal_core_eunits())
    assert len(cores) == num_cores
    for core in cores:
        exp_portions = director.compute_explanation(core)
        assert set(ep.id_ for ep in exp_portions) in ids_in_cores

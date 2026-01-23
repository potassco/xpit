"""utility fixtures for tests."""

from typing import Callable

import clingo
import pytest

from xpit.director.director import ExplanationDirector


@pytest.fixture(name="director_factory")
def fixture_director_factory() -> Callable[[int], ExplanationDirector]:
    """creates ExplanationDirector instances for testing."""

    def _create_director(num_eunits: int) -> ExplanationDirector:
        ctl = clingo.Control()
        return ExplanationDirector(ctl, num_eunits)

    return _create_director

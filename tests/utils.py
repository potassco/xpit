"""utility fixtures for tests."""

from typing import Callable, Optional

import clingo
import pytest

from xpit.director.director import ExplanationDirector


@pytest.fixture(name="director_factory")
def fixture_director_factory() -> Callable[[Optional[int]], ExplanationDirector]:
    """creates ExplanationDirector instances for testing."""

    def _create_director(num_eunits: Optional[int] = None) -> ExplanationDirector:
        ctl = clingo.Control()
        return ExplanationDirector(ctl, num_eunits)

    return _create_director

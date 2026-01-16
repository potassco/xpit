import clingo
import pytest

from xpit.director.director import ExplanationDirector
from xpit.explainer.program import ProgramExplainer


@pytest.fixture
def director_factory():
    def _create_director(num_eunits):
        ctl = clingo.Control()
        return ExplanationDirector(ctl, num_eunits)

    return _create_director

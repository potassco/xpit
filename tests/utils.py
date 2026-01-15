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


@pytest.fixture
def explainer_factory():
    def _create_explainer(director, type_="program", lp_files=None):
        if type_ == "program":
            return ProgramExplainer(director=director, lp_files=lp_files or [])
        # Add other explainer types as needed
        else:
            raise ValueError(f"Unknown explainer type: {type_}")

    return _create_explainer

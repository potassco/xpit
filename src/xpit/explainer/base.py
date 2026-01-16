"""
Explainer abstract class
"""

from abc import ABC, abstractmethod
from typing import List

import clingo

# from ..director import ExpDirector
# TODO: check for a better way of handling circular imports in Python
import xpit.director as director

from ..definitions import ExplainablePortion as EPortion
from ..definitions import ExplanationUnit as EUnit


class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self) -> None:
        self.control: clingo.Control = None

    def set_control(self, control: clingo.Control) -> None:
        self.control = control

    @abstractmethod
    def setup_before_grounding(self) -> int:  # nocoverage
        pass

    @abstractmethod
    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:  # nocoverage
        pass

    @abstractmethod
    def get_explainable_portions(self, eunit: EUnit) -> List[EPortion]:  # nocoverage
        pass

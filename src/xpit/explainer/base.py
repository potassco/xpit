"""
Explainer abstract class
"""

from typing import List
from abc import ABC, abstractmethod

import clingo

# from ..director import ExpDirector
# TODO: check for a better way of handling circular imports in Python
import xpit.director as director

from ..definitions import ExplanationUnit as EUnit
from ..definitions import ExplainablePortion as EPortion

class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self, director: director.ExplanationDirector) -> None:
        self.director = director
        self.control: clingo.Control = self.director.control

    @abstractmethod
    def setup_before_grounding(self) -> int:
        pass

    @abstractmethod
    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:
        pass

    @abstractmethod
    def get_explainable_portions(self, eunit: EUnit) -> List[EPortion]:
        pass

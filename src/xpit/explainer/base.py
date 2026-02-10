"""
Explainer abstract class
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import clingo

from xpit.definitions import ExplanationPortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit


class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self) -> None:
        """initializes the explainer instance"""
        self.control: Optional[clingo.Control] = None

    def set_control(self, control: clingo.Control) -> None:
        """sets the clingo control object for the explainer"""
        self.control = control

    @abstractmethod
    def get_eunit_request(self) -> int:
        """gets the number of eunits requested by the explainer"""

    @abstractmethod
    def setup_before_grounding(self) -> None:  # nocoverage
        """sets up the explainer before grounding"""

    @abstractmethod
    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:  # nocoverage
        """assigns eunit budget to explanation portions"""

    @abstractmethod
    def get_explanation_portions(self, eunit: EUnit) -> List[EPortion]:  # nocoverage
        """gets the explanation portions bound to the given eunit"""

"""
Explainer abstract class
"""

from abc import ABC, abstractmethod
from typing import List, Optional

import clingo

from xpit.definitions import ExplanationPortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit
from xpit.definitions.define import PortionId, PortionIdFilter


class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self) -> None:
        """initializes the explainer instance"""
        self.control: Optional[clingo.Control] = None
        self.tag_filter: Optional[PortionIdFilter] = None

    def set_control(self, control: clingo.Control) -> None:
        """sets the clingo control object for the explainer"""
        self.control = control

    def add_tag_filter(self, tag_filter: PortionIdFilter) -> None:
        """adds a tag filter to the explainer"""
        if self.tag_filter is not None:
            self.tag_filter.extend(tag_filter.tags)
        else:
            self.tag_filter = tag_filter

    def clear_tag_filter(self) -> None:
        """clears the tag filter from the explainer"""
        self.tag_filter = None

    def append_portion_id(self, portion_id: str | PortionId) -> None:
        """appends a portion id to the explainer's tag filter"""
        if self.tag_filter is not None:
            self.tag_filter.append(portion_id)
        else:
            self.tag_filter = PortionIdFilter([portion_id])

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

"""
ASP Program based explainer
"""

from pathlib import Path
from typing import Sequence, Union

from .base import Explainer

import clingo
from ..director import ExpDirector


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for tagged rules of input logic programs,
    which are explainable portions.
    It also binds eunits from the assigned budget to explainable portions.
    """

    def __init__(self, control: clingo.Control, director: ExpDirector, lp_files: Sequence[Union[str,Path]]) -> None:
        super().__init__(control, director)
        self.lp_files = lp_files

    def get_explainable_portions(self) -> 


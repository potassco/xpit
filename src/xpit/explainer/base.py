"""
Explainer abstract class
"""

from abc import ABC, abstractmethod

import clingo
# from ..director import ExpDirector
import xpit.director

class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self, control: clingo.Control, director: ExpDirector) -> None:
        self.control = control
        self.director = director


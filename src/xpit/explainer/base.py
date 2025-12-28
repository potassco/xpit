"""
Explainer abstract class
"""

from abc import ABC, abstractmethod

import clingo
# from ..director import ExpDirector
# TODO: check for a better way of handling circular imports in Python
import xpit.director

class Explainer(ABC):
    """
    Abstract Explainer class
    """

    def __init__(self, director: ExpDirector) -> None:
        self.director = director
        self.control: clingo.Control = self.director.control

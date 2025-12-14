from typing import List

from ..explainer import Explainer

import clingo


# @dataclass
class EUnit:
    """
    Container class for the Explanation Unit (eunit)
    """

    literal: int


class ExpDirector:
    """
    Explanation Director class that manages explainer modules and allocates an eunit budget.
    """

    def __init__(self, control: clingo.Control, maximum_number_of_eunits: int) -> None:
        self.control = control
        self.maximum_number_of_eunits = maximum_number_of_eunits
        self.explainers: List[Explainer] = []

    def register_explainer(self, explainer: Explainer) -> None:
        self.explainers.append(explainer)



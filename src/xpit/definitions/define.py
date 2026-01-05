"""
Class definitions for explanation related abstractions
"""

from dataclasses import dataclass

from clingo.symbolic_atoms import SymbolicAtom

@dataclass
class EUnit:
    """
    Container class for the Explanation Unit (eunit)
    """

    assumption_lit: int = 0

    def __hash__(self):
        return hash(self.assumption_lit)


@dataclass
class ExpPortion:
    """
    Container class for the explainable portion
    """

    id_: str
    exp_atom: SymbolicAtom

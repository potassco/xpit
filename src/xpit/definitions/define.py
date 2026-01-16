"""
Class definitions for explanation related abstractions
"""

from dataclasses import dataclass

from clingo.symbolic_atoms import SymbolicAtom


@dataclass
class ExplanationUnit:
    """
    Container class for the Explanation Unit (eunit)
    """

    assumption_lit: int

    def __hash__(self):
        return hash(self.assumption_lit)


@dataclass
class ExplainablePortion:
    """
    Container class for the Explainable Portion
    """

    id_: str
    exp_atom: SymbolicAtom

    def __repr__(self):  # nocoverage
        return "ExplainablePortion(id=%s, exp_atom=%s)" % (self.id_, str(self.exp_atom.symbol))

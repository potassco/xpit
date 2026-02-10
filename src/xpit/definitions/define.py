"""
Class definitions for explanation related abstractions
"""

from dataclasses import dataclass

from clingo.symbolic_atoms import SymbolicAtom

from xpit.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExplanationUnit:
    """
    Container class for the Explanation Unit (eunit)
    """

    assumption_lit: int

    def __hash__(self) -> int:
        return hash(self.assumption_lit)


@dataclass
class ExplainablePortion:
    """
    Container class for the Explainable Portion
    """

    id_: str
    exp_atom: SymbolicAtom

    # TODO: use clorm for the exp_atom

    def __repr__(self) -> str:  # nocoverage
        return f"ExplainablePortion(id={self.id_}, exp_atom={self.exp_atom.symbol})"

    def get_message(self) -> str:
        """returns the message formatted using load"""
        try:
            msg_data = tuple(str(d) for d in self.exp_atom.symbol.arguments[1].arguments[1].arguments)
            return str(self.exp_atom.symbol.arguments[1].arguments[0]).format(*msg_data)
        except Exception as err:
            logger.error("The message of the eportion cannot be processed: %s", self)
            raise err

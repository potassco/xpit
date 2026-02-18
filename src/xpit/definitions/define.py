"""
Class definitions for explanation related abstractions
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import clingo
import clingo.ast
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
class ExplanationPortion:
    """
    Container class for the Explanation Portion
    """

    id_: str
    exp_atom: SymbolicAtom

    # TODO: use clorm for the exp_atom

    def __repr__(self) -> str:  # nocoverage
        return f"ExplanationPortion(id={self.id_}, exp_atom={self.exp_atom.symbol})"

    def get_message(self) -> str:  # nocoverage
        """returns the message formatted using load"""
        try:
            msg_data = tuple(str(d) for d in self.exp_atom.symbol.arguments[1].arguments[1].arguments)
            return str(self.exp_atom.symbol.arguments[1].arguments[0]).format(*msg_data)
        except Exception as err:
            logger.error("The message of the eportion cannot be processed: %s", self)
            raise err


WildCardArgument = Enum("WildCardArgument", "*")  # TODO: use for tagging


class Argument:
    """Class representing an argument for rule tags."""

    def __init__(
        self,
        value: (
            str | int | re.Pattern | Callable[[str], bool] | Callable[[int], bool] | list["Argument"] | WildCardArgument
        ),
    ) -> None:
        """initializes an Argument with a value that can be a:
        string, integer (string and int are treated as concrete values),
        regex pattern, callable, list of Arguments (treated as concrete if all are concrete), or a wildcard."""
        self.value = value
        self.is_concrete = isinstance(value, (str, int))
        if isinstance(value, list):
            self.is_concrete = all(arg.is_concrete for arg in value)

    @classmethod
    def from_ast(cls, arg: clingo.ast.AST):
        if arg.ast_type == clingo.ast.ASTType.SymbolicTerm:
            wrapped_value = arg.values()[1]
            if wrapped_value.type == clingo.symbol.SymbolType.Number:
                value = wrapped_value.number
            elif wrapped_value.type == clingo.symbol.SymbolType.String:
                value = wrapped_value.string
            elif wrapped_value.type == clingo.symbol.SymbolType.Function:
                value = wrapped_value.name
                assert isinstance(value, str)
            else:
                raise NotImplemented("Infimum and Supremum are not supported as Symbol type in tags.")
            return Argument(value)
        if arg.ast_type == clingo.ast.ASTType.Variable:
            return Argument(WildCardArgument["*"])
        if arg.ast_type == clingo.ast.ASTType.Function:
            value = [cls.from_ast(arg_i) for arg_i in arg.arguments]
            return Argument(value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Argument):
            raise NotImplemented(f"__eq__ not implemented for type other than Argument.")
        if type(self.value) != type(other.value):
            return False
        return self.value == other.value

    def allows(self, other: "Argument") -> bool:
        """Checks if this argument matches another concrete argument based on type and value."""
        if not other.is_concrete:
            raise ValueError(f"Other argument must be concrete (string or integer) for matching. Got: {other.value}")
        if isinstance(self.value, WildCardArgument):
            return True
        if isinstance(self.value, re.Pattern):
            if not isinstance(other.value, str) or not re.match(self.value, other.value):
                return False
        elif callable(self.value):
            if isinstance(other.value, str) or isinstance(other.value, int):
                return self.value(other.value)
        elif isinstance(self.value, list):
            if not isinstance(other.value, list) or len(self.value) != len(other.value):
                return False
            for arg_self, arg_other in zip(self.value, other.value):
                if not arg_self.allows(arg_other):
                    return False
        else:
            if self.value != other.value:
                return False
        return True


class TagId:
    """Class representing a tag id for explanation portions."""

    def __init__(
        self,
        name: str,
        arity: Optional[int] = None,
        arguments: Optional[
            list[
                Argument
                | str
                | int
                | re.Pattern
                | Callable[[str], bool]
                | Callable[[int], bool]
                | list["Argument"]
                | WildCardArgument
            ]
        ] = None,
    ) -> None:
        self.name = name
        assert arity is None or arity >= 0, "Arity must be a non-negative integer or None"
        assert arity is not None or arguments is None, "Arguments must be None if arity is None"
        assert arguments is None or len(arguments) == arity, "Number of arguments must match the arity"
        self.arity = arity
        if arguments is None:
            self.arguments = None
        else:
            self.arguments = []
            for arg in arguments:
                if not isinstance(arg, (Argument)):
                    self.arguments.append(Argument(arg))
                else:
                    self.arguments.append(arg)

    def __str__(self) -> str:
        if self.arity is None:
            return f"{self.name}/*"
        if self.arity == 0:
            return self.name
        else:
            return f"{self.name}/{self.arity}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TagId):
            raise NotImplemented(f"Comparisons of TagId with objects of type not implemented: {other} ")
        if (self.name, self.arity) != (other.name, other.arity):
            return False
        if self.arguments is None:
            return other.arguments is None
        if len(self.arguments) != len(other.arguments):
            return False
        return all(s == o for s, o in zip(self.arguments, other.arguments))

    @classmethod
    def from_ast(cls, arg: clingo.ast.AST, sig_only=True) -> "TagId":
        """Construct a TagId from a clingo AST argument (SymbolicTerm or Function)."""
        if arg.ast_type == clingo.ast.ASTType.SymbolicTerm:
            return cls(arg.symbol.name, 0)
        if arg.ast_type == clingo.ast.ASTType.Function:
            if sig_only:
                return cls(arg.name, len(arg.arguments))
            return cls(arg.name, len(arg.arguments), [Argument.from_ast(arg_i) for arg_i in arg.arguments])
        raise ValueError(f"Invalid argument for _explain: {arg}. Expected a symbolic or function term.")

    @classmethod
    def from_clingo_symbol(cls, symbol: clingo.symbol.Symbol) -> "TagId":
        """Construct a TagId from a clingo Symbol (Function or String)."""
        if symbol.type == clingo.SymbolType.Function:
            arguments = [Argument(cls._convert_clingo_symbol_to_argument(a)) for a in symbol.arguments]
            return cls(symbol.name, len(symbol.arguments), arguments)
        if symbol.type == clingo.SymbolType.String:
            return cls(symbol.string, 0, [])
        raise ValueError(f"Invalid symbol for TagId: {symbol}. Expected a function or string symbol.")

    @staticmethod
    def _convert_clingo_symbol_to_argument(symbol: clingo.symbol.Symbol) -> Argument:
        """Converts a clingo symbol to an Argument instance."""
        if symbol.type == clingo.SymbolType.Number:
            return Argument(symbol.number)
        if symbol.type == clingo.SymbolType.String:
            return Argument(symbol.string)
        if symbol.type == clingo.SymbolType.Function:
            # For nested functions, we can represent them as lists of arguments
            nested_arguments = [TagId._convert_clingo_symbol_to_argument(a) for a in symbol.arguments]
            return Argument(nested_arguments)
        raise ValueError(f"Unsupported clingo symbol type for argument conversion: {symbol}")

    def is_tag_active(self, tag_filters: Optional["list[TagId]"] = None) -> bool:  # TODO: type of tag_filter
        """Checks if the given tag is active based on the explainable portion ids."""
        if tag_filters is None:
            return True
        return any(tag_filter.allows(self) for tag_filter in tag_filters)

    def allows(self, other: "TagId") -> bool:
        """Checks if this TagId allows another TagId based on name, arity, and arguments."""
        if not isinstance(other, TagId):
            return NotImplemented
        if self.name != other.name:
            return False
        if self.arity is None:
            return True
        if self.arity != other.arity:
            return False
        if self.arguments is None:
            return True
        if len(self.arguments) != len(other.arguments):
            return False
        return all(arg_self.matches(arg_other) for arg_self, arg_other in zip(self.arguments, other.arguments))


class TagIdFilter:
    """Class representing a tag filter for explanation portions."""

    def __init__(self, tags: list[TagId | str]) -> None:
        """Initializes a TagIdFilter with a list of TagIds or strings
        (which are converted to TagIds with arity given (or None if not specified)).
        The filter allows tags that match any of the provided tags."""
        self.tags = []
        for tag in tags:
            self.append(tag)

    def __len__(self) -> int:
        return len(self.tags)

    def append(self, tag: TagId | str) -> None:
        """Appends a new tag to the filter."""
        if isinstance(tag, TagId):
            self.tags.append(tag)
        elif isinstance(tag, str):
            tag_parts = tag.split("/")
            if len(tag_parts) == 2:
                tag_id, arity_str = tag_parts
                try:
                    arity = int(arity_str)
                    self.tags.append(TagId(tag_id, arity))
                except ValueError:
                    raise ValueError(f"Invalid tag format: {tag}. Expected 'tag_id/arity' where arity is an integer.")
            elif len(tag_parts) == 1:
                self.tags.append(TagId(tag_parts[0], None))
            else:
                raise ValueError(f"Invalid tag format: {tag}. Expected 'tag_id' or 'tag_id/arity'.")

    def allows(self, tag: TagId) -> bool:
        """Checks if the given tag is allowed by the filter."""
        return any(tag_filter.allows(tag) for tag_filter in self.tags)

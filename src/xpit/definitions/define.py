"""
Class definitions for explanation related abstractions
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Protocol, Self, Sequence, cast, overload

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

    id_: "PortionId"
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


class WildCardArgument(Enum):
    """Wildcard enum for allowing all values in an Argument"""

    WILDCARD = "*"


class StrIntPredicate(Protocol):
    """Protocoll for mypy to deal with callable int->bool and str->bool"""

    @overload
    def __call__(self, x: str) -> bool: ...
    @overload
    def __call__(self, x: int) -> bool: ...


class Argument:
    """Class representing an argument for rule tags."""

    def __init__(
        self,
        value: (
            str
            | int
            | Callable[[str], bool]
            | Callable[[int], bool]
            | list["Argument"]
            | tuple[str, list["Argument"]]
            | WildCardArgument
        ),
    ) -> None:
        """initializes an Argument with a value that can be a:
        string, integer (string and int are treated as concrete values),
        regex pattern, callable, list of Arguments (treated as concrete if all are concrete), or a wildcard."""
        self.value: str | int | StrIntPredicate | list["Argument"] | tuple[str, list["Argument"]] | WildCardArgument
        if callable(value):
            self.value = cast(StrIntPredicate, value)
        else:
            self.value = value
        self.is_concrete = isinstance(value, (str, int))
        if isinstance(value, list):
            self.is_concrete = all(arg.is_concrete for arg in value)
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], list):
            self.is_concrete = all(arg.is_concrete for arg in value[1])

    def __repr__(self) -> str:
        if isinstance(self.value, list):
            return f"({', '.join(repr(arg) for arg in self.value)})"
        if isinstance(self.value, WildCardArgument):
            return "*"
        if callable(self.value):
            return f"<callable {self.value}>"
        return f"{self.value}"

    def unpack(self) -> Any:
        """Unpacks the argument value for use in filters."""
        if not self.is_concrete:
            raise ValueError(f"Cannot unpack non-concrete argument: {self.value}")
        if isinstance(self.value, list):
            return [arg.unpack() for arg in self.value]
        if isinstance(self.value, tuple) and len(self.value) == 2 and isinstance(self.value[0], str):
            return (self.value[0], [arg.unpack() for arg in self.value[1]])
        return self.value

    @classmethod
    def from_ast(cls, arg: clingo.ast.AST) -> "Argument":
        """Create Argument from clingo ast"""
        if arg.ast_type == clingo.ast.ASTType.SymbolicTerm:
            value: str | int | list["Argument"] | WildCardArgument
            wrapped_value = arg.values()[1]
            assert isinstance(wrapped_value, clingo.symbol.Symbol)
            if wrapped_value.type == clingo.symbol.SymbolType.Number:
                value = wrapped_value.number
            elif wrapped_value.type == clingo.symbol.SymbolType.String:
                value = wrapped_value.string
            elif wrapped_value.type == clingo.symbol.SymbolType.Function:
                value = wrapped_value.name
                assert isinstance(value, str)
            else:  # nocoverage
                raise NotImplementedError("Infimum and Supremum are not supported as Symbol type in tags yet.")
            return Argument(value)
        if arg.ast_type == clingo.ast.ASTType.Variable:
            return Argument(WildCardArgument("*"))
        if arg.ast_type == clingo.ast.ASTType.Function:
            value = [cls.from_ast(arg_i) for arg_i in arg.arguments]
            if arg.name:
                return Argument((arg.name, value))
            return Argument(value)
        raise ValueError(f"Could not create Argument from clingo ast input: {arg}")  # nocoverage

    @classmethod
    def from_clingo_symbol(cls, symbol: clingo.symbol.Symbol) -> "Argument":
        """Converts a clingo symbol to an Argument instance."""
        if symbol.type == clingo.SymbolType.Number:
            return Argument(symbol.number)
        if symbol.type == clingo.SymbolType.String:
            return Argument(symbol.string)
        if symbol.type == clingo.SymbolType.Function:
            if not symbol.arguments and symbol.name:
                return Argument(symbol.name)

            # For nested functions, we can represent them as lists of arguments
            nested_arguments = [cls.from_clingo_symbol(a) for a in symbol.arguments]
            if symbol.name:
                return Argument((symbol.name, nested_arguments))
            return Argument(nested_arguments)
        raise ValueError(f"Unsupported clingo symbol type for argument conversion: {symbol}")  # nocoverage

    def allows(self, other: Self) -> bool:
        """Checks if this argument matches another concrete argument based on type and value."""
        if self.value in WildCardArgument:
            return True
        if other.value in WildCardArgument:  # nocoverage
            return True
        if not other.is_concrete:
            raise ValueError(f"Other argument must be concrete (string or integer) for matching. Got: {other.value}")
        if callable(self.value):
            if isinstance(other.value, (str, int)):
                return self.value(other.value)
        elif isinstance(self.value, list):
            if not isinstance(other.value, list) or len(self.value) != len(other.value):
                return False
            return all(arg_self.allows(arg_other) for arg_self, arg_other in zip(self.value, other.value))
        elif isinstance(self.value, tuple):
            if not isinstance(other.value, tuple):  # nocoverage
                return False
            if self.value[0] != other.value[0]:  # nocoverage
                return False
            return all(arg_self.allows(arg_other) for arg_self, arg_other in zip(self.value[1], other.value[1]))
        else:
            if self.value != other.value:
                return False
        return True


class PortionId:
    """Class representing a tag id for explanation portions."""

    def __init__(
        self,
        name: str,
        arity: Optional[int] = None,
        arguments: Optional[
            Sequence[
                Argument | str | int | Callable[[str], bool] | Callable[[int], bool] | list[Argument] | WildCardArgument
            ]
            | Callable[[Any], bool]
        ] = None,
    ) -> None:
        self.name = name
        if arity is not None and arity < 0:
            raise ValueError("Arity must be a non-negative integer or None")  # nocoverage
        if arity is None and arguments is not None:
            raise ValueError("Arguments must be None if arity is None")  # nocoverage
        # if arguments is not None and len(arguments) != arity:
        #     raise ValueError("Number of arguments must match the arity")
        self.arity = arity
        self.arguments: Optional[Sequence[Argument] | Callable[[Any], bool]]
        if arguments is None:
            self.arguments = None
        else:
            if callable(arguments):  # nocoverage
                self.arguments = arguments
            else:
                self.arguments = []
                for arg in arguments:
                    if not isinstance(arg, (Argument)):
                        self.arguments.append(Argument(arg))
                    else:
                        self.arguments.append(arg)

    @classmethod
    def from_str(cls, tag_str: str) -> "PortionId":
        """creates a TagId from a string."""
        tag_parts = tag_str.split("/")
        if len(tag_parts) == 2:
            tag_id, arity_str = tag_parts
            try:
                arity = int(arity_str)
                return PortionId(tag_id, arity)
            except ValueError as exc:  # nocoverage
                raise ValueError(
                    f"Invalid tag format: {tag_str}. Expected 'tag_id/arity' where arity is an integer."
                ) from exc
        elif len(tag_parts) == 1:
            return PortionId(tag_parts[0], None)
        else:  # nocoverage
            raise ValueError(f"Invalid tag format: {tag_str}. Expected 'tag_id' or 'tag_id/arity'.")

    def __repr__(self) -> str:
        if self.arity is None:
            return f"{self.name}/*"
        if self.arity == 0:
            return self.name
        if self.arguments is None:
            return f"{self.name}/{self.arity}"
        if callable(self.arguments):
            return f"{self.name}({self.arguments})"
        return f"{self.name}({', '.join(repr(arg) for arg in self.arguments)})"

    @classmethod
    def from_ast(cls, arg: clingo.ast.AST, sig_only: bool = True) -> "PortionId":
        """Construct a TagId from a clingo AST argument (SymbolicTerm or Function)."""
        if arg.ast_type == clingo.ast.ASTType.SymbolicTerm:
            if arg.symbol.type == clingo.SymbolType.String:
                return cls(arg.symbol.string, 0)
            if arg.symbol.type == clingo.SymbolType.Function:
                return cls(arg.symbol.name, 0)
            raise ValueError(  # nocoverage
                f"Invalid Id for tag: {arg}."
                "First argument to _explain/2 is used as Id and must be a predicate(recommended), "
                "a string or a symbolic constant(disencouraged)"
            )
        if arg.ast_type == clingo.ast.ASTType.Function:
            if sig_only:
                return cls(arg.name, len(arg.arguments))
            return cls(arg.name, len(arg.arguments), [Argument.from_ast(arg_i) for arg_i in arg.arguments])
        raise ValueError(f"Invalid argument for _explain: {arg}. Expected a symbolic or function term.")  # nocoverage

    @classmethod
    def from_clingo_symbol(cls, symbol: clingo.symbol.Symbol) -> "PortionId":
        """Construct a TagId from a clingo Symbol (Function or String)."""
        if symbol.type == clingo.SymbolType.Function:
            arguments = [Argument.from_clingo_symbol(a) for a in symbol.arguments]
            return cls(symbol.name, len(symbol.arguments), arguments)
        if symbol.type == clingo.SymbolType.String:
            return cls(symbol.string, 0)
        raise ValueError(f"Invalid symbol for TagId: {symbol}. Expected a function or string symbol.")  # nocoverage

    def allows(self, other: Self) -> bool:
        """Checks if this TagId allows another TagId based on name, arity, and arguments."""
        if not isinstance(other, PortionId):  # nocoverage
            return ValueError("other: %s must be a TagId", other)
        if self.name != other.name:
            return False
        if self.arity is None:
            return True
        if self.arity != other.arity:  # nocoverage
            return False
        if self.arguments is None:
            return True
        if not isinstance(other.arguments, Sequence):
            logger.error(
                "Expected other.arguments to be a Sequence for callable argument filter, got: %s", other.arguments
            )
            return False
        if callable(self.arguments):
            try:
                return self.arguments(*[arg.unpack() for arg in other.arguments])
            except ValueError as e:
                logger.error("Error unpacking arguments: %s", e)
            except TypeError as e:
                logger.error("Error applying callable argument filter: %s", e)
            return False
        return all(arg_self.allows(arg_other) for arg_self, arg_other in zip(self.arguments, other.arguments))


class PortionIdFilter:
    """Class representing a tag filter for explanation portions."""

    def __init__(self, tags: list[PortionId | str]) -> None:
        """Initializes a TagIdFilter with a list of TagIds or strings
        (which are converted to TagIds with arity given (or None if not specified)).
        The filter allows tags that match any of the provided tags."""
        self.tags: list[PortionId] = []
        for tag in tags:
            if isinstance(tag, PortionId):
                self.tags.append(tag)
            elif isinstance(tag, str):
                self.tags.append(PortionId.from_str(tag))

    def __len__(self) -> int:
        return len(self.tags)

    def append(self, tag: PortionId | str) -> None:
        """Appends a new tag to the filter."""
        if isinstance(tag, PortionId):
            self.tags.append(tag)
        elif isinstance(tag, str):
            self.tags.append(PortionId.from_str(tag))

    def extend(self, tags: Sequence[PortionId | str]) -> None:
        """Extends the filter with a list of new tags."""
        for tag in tags:
            self.append(tag)

    def allows(self, tag: PortionId) -> bool:
        """Checks if the given tag is allowed by the filter."""
        return any(tag_filter.allows(tag) for tag_filter in self.tags)

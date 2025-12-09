"""Explanation Director Prototype Application"""

import sys
from collections import defaultdict
from copy import deepcopy
from textwrap import dedent
from typing import Optional, Sequence

import clingo.symbol as clisym
from clingexplaid.mus import CoreComputer
from clingo import ApplicationOptions, Control, String, SymbolicAtom, SymbolType
from clingo.application import Application, clingo_main
from clingo.ast import (
    AST,
    Aggregate,
    ASTType,
    ComparisonOperator,
    ConditionalLiteral,
    Guard,
    ProgramBuilder,
    Rule,
    Sign,
    SymbolicTerm,
    Transformer,
    parse_files,
)
from clingo.backend import Observer
from clingo.symbol import parse_term
from clingox.ast import location_to_str

from explanation_director_prototype.utils.logging import get_logger

log = get_logger("main")


class ExplanationTransformer(Transformer):
    """
    Transformer to modify rules marked for explanation. Marked rules contain a literal of the form
    _explain/2 in their body."""

    def __init__(self) -> None:
        """Initialize the Explanation Transformer."""
        self._location_dict: defaultdict[tuple[str, str], list[tuple[int, int, int]]] = defaultdict(list)

    def visit_Rule(self, ast: AST) -> AST:  # pylint: disable=invalid-name
        """Visit a rule AST node and transform it if it is marked for explanation."""
        is_marked_for_explanation = False

        for lit in ast.body:
            if (
                lit.ast_type == ASTType.Literal
                and lit.atom.ast_type == ASTType.SymbolicAtom
                and lit.atom.symbol.ast_type == ASTType.Function
                and lit.atom.symbol.name == "_explain"
            ):
                exp_lit = deepcopy(lit)
                exp_lit.atom.symbol.name = "_exp"
                exp_lit.sign = Sign.NoSign
                is_marked_for_explanation = True
                break

        if is_marked_for_explanation:
            new_rule = Rule(
                ast.location,
                Aggregate(
                    ast.location,
                    Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1"))),
                    [ConditionalLiteral(ast.location, ast.head, []), ConditionalLiteral(ast.location, exp_lit, [])],
                    Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1"))),
                ),
                ast.body,
            )
            self._add_to_location_dict(exp_lit, ast)

            return new_rule
        return ast

    def _add_to_location_dict(self, literal, ast) -> None:
        """Add location info to the location dictionary"""
        symbol = self._parse_literal(literal)
        self._location_dict[symbol].append(location_to_str(ast.location))

        # key = self.parse_symbol_arguments(literal)
        # loc = self.get_location(literal)
        # self._location_dict[key].append(loc)

    def _parse_ast_dict(self, ast_dict: dict) -> None:
        """Parse AST dictionary to extract relevant information"""
        for key, value in ast_dict.items():
            if key == "ast_type" and value == "Literal":  # root
                ast_dict.get("atom", {})

    def get_location(self, literal) -> None:
        """Extract location from literal"""
        return literal.location

    def _parse_function(self, ast_function) -> clisym.Function:
        """Parse function arguments from AST function dictionary"""
        args = []
        for arg in ast_function.arguments:
            parsed_arg = self._parse_term(arg)
            if parsed_arg is not None:
                args.append(parsed_arg)

        return clisym.Function(ast_function.name, args, True)

    def _parse_literal(self, ast_literal) -> clisym.Symbol:

        if ast_literal.atom.ast_type == ASTType.SymbolicAtom:
            return self._parse_symbolic_atom(ast_literal.atom)
        raise NotImplementedError("Only SymbolicAtom supported in _explain.")

    def _parse_symbolic_atom(self, ast_symbolic_atom) -> Optional[clisym.Symbol]:
        return self._parse_term(ast_symbolic_atom.symbol)

    def _parse_term(self, ast_term) -> Optional[clisym.Symbol]:
        if ast_term.ast_type == ASTType.Function:
            return self._parse_function(ast_term)
        if ast_term.ast_type == ASTType.SymbolicTerm:
            return self._parse_symbolic_term(ast_term)
        if ast_term.ast_type == ASTType.Variable:
            return String("{}")  # Placeholder for variable handling
        if ast_term.ast_type == ASTType.UnaryOperation:
            raise NotImplementedError("UnaryOperation in _explain not supported yet.")
        if ast_term.ast_type == ASTType.BinaryOperation:
            raise NotImplementedError("BinaryOperation in _explain not supported yet.")
        if ast_term.ast_type == ASTType.Interval:
            raise NotImplementedError("Interval in _explain not supported yet.")
        if ast_term.ast_type == ASTType.Pool:
            raise NotImplementedError("Pool in _explain not supported yet.")

    def _parse_symbolic_term(self, ast_symbolic_term) -> clisym.Symbol:
        return ast_symbolic_term.symbol

    def _parse_variable(self, ast_variable) -> None:
        pass

    def parse_symbol_arguments(self, literal):
        """Parse a symbol to extract its arguments."""
        assert literal.ast_type == ASTType.Literal
        symbol = literal.atom.symbol
        assert symbol.ast_type == ASTType.Function
        assert symbol.name == "_exp"
        for arg in symbol.arguments:
            if arg.ast_type == ASTType.Function:
                pass
            if arg.ast_type == ASTType.SymbolicTerm:
                arg_symbol = arg.symbol
                assert arg_symbol.ast_type == ASTType.Function
                arg_symbol.name
                if arg_symbol.arguments:
                    pass  # TODO: what happens to (possible) arguments? or to a strange inner structure? _exp((xxx, yyy), "msg")?

        if literal.type == SymbolType.Function:
            return (literal.name, len(literal.arguments))
        return (str(literal), 0)  # nocoverage

    def get_location_dict(self) -> dict:
        """Get the location dictionary."""
        return self._location_dict


class ExpObserver(Observer):
    """Observer to monitor the grounding process."""

    # def rule(self, choice, head, body):
    #     """Called when a rule is added to the program."""
    #     pass

    # def theory_term_string(self, term_id: int, name: str) -> None:
    #     """Called when a theory term string is encountered."""
    #     print(term_id, name)


class ExpDirectorProto(Application):
    """Explanation Director Prototype Application"""

    def __init__(self) -> None:
        """Initialize the Explanation Director Prototype Application."""
        self.program_name = "exp_director"
        self.version = "0.1"
        self._num_of_assumptions: int = 10
        self._assumption_budget: list[int] = []
        self._mapping: defaultdict[int, list[SymbolicAtom]] = defaultdict(list)
        self._loc_mapping: defaultdict[SymbolicAtom, list[str]] = defaultdict(list)

    def set_number_of_assumptions(self, val: str) -> bool:
        """Set the number of assumptions in the budget."""
        self._num_of_assumptions = int(val)
        return True

    def _create_assumption_budget(self, ctl: Control, num: int) -> None:
        """Create an assumption budget with a specified number of assumptions."""
        with ctl.backend() as backend:
            for i in range(num):
                sym = clisym.Function("assumption" + str(i + 1))
                atm = backend.add_atom(sym)
                self._assumption_budget.append(atm)
                backend.add_rule(head=[atm], choice=True)

    def _use_assumption_budget(self, ctl: Control) -> None:
        """Use the assumption budget to control explainable literals."""
        log.debug("Setting the assumptions...")
        with ctl.backend() as backend:
            idx = 0
            for a in ctl.symbolic_atoms.by_signature("_exp", 2):
                log.debug("%s %s mapped to %s", a.symbol, a.literal, self._assumption_budget[idx])
                backend.add_rule(head=[], body=[a.literal, self._assumption_budget[idx]])  # :- _exp(...), assumptionX.
                backend.add_rule(
                    head=[a.literal], body=[-1 * self._assumption_budget[idx]], choice=False
                )  # _exp(...) :- not assumptionX.
                self._mapping[self._assumption_budget[idx]].append(a)
                if (idx + 1) < self._num_of_assumptions:
                    idx += 1

    def register_options(self, options: ApplicationOptions) -> None:
        """Register command-line options for the application."""
        log.debug("Registering options...")
        group = "Explanation director options"

        options.add(
            group,
            "assumpt-num",
            dedent(
                """\
                Set the number of assumptions in the budget.
                """
            ),
            self.set_number_of_assumptions,
            argument="<num-of-assumptions>",
        )

    def core_to_str(self, core: list[int]) -> str:
        """Print the core literals with their corresponding messages."""
        result = ""
        result += f"Core literals: {core}\n"
        for l in core:
            if l in self._mapping:
                result += f"Explanation for assumption {l}:\n"
                for a in self._mapping[l]:
                    result += "    " + self.format_explanation_symbol(a.symbol) + "\n"
                    result += "    Location(s): " + ", ".join(self._loc_mapping[a.symbol]) + "\n"
        return result

    def format_explanation_symbol(self, symbol: clisym.Symbol) -> str:
        """Format the explanation for a given symbol."""
        if symbol.type == SymbolType.Function and symbol.name == "_exp":
            msg = symbol.arguments[1].arguments[0].string
            if symbol.arguments[1].arguments[1].type == SymbolType.Function:
                args = symbol.arguments[1].arguments[1].arguments
            else:
                args = [symbol.arguments[1].arguments[1]]
            return msg.format(*[str(arg) for arg in args])
        # unexpected symbol
        return str(symbol)  # nocoverage

    def _is_instanciation_of_rec(self, symbol: clisym.Symbol, schema: clisym.Symbol) -> bool:
        """Check if a symbol is an instanciation of a given schema."""
        if schema.type == SymbolType.Function:
            if (
                symbol.type != SymbolType.Function
                or symbol.name != schema.name
                or len(symbol.arguments) != len(schema.arguments)
            ):
                return False
            for sym_arg, schema_arg in zip(symbol.arguments, schema.arguments):
                if not self._is_instanciation_of_rec(sym_arg, schema_arg):
                    return False
            return True
        if schema.type == SymbolType.String:
            return (
                schema.string == "{}"  # wildcard for Variables
                or symbol.type == SymbolType.String
                and schema.string == symbol.string
            )
        if schema.type == SymbolType.Number:
            return symbol.type == SymbolType.Number and schema.number == symbol.number
        return schema.type == symbol.type

    def _is_instanciation_of(self, symbol: clisym.Symbol, schema: clisym.Symbol) -> bool:
        assert symbol.name == "_exp", "Only _exp symbols are supported."
        assert len(symbol.arguments) == 2, "_exp symbols must have exactly two arguments."
        if symbol.name != schema.name or len(symbol.arguments) != len(schema.arguments) or symbol.type != schema.type:
            return False
        for sym_arg, schema_arg in zip(symbol.arguments, schema.arguments):
            if not self._is_instanciation_of_rec(sym_arg, schema_arg):
                return False
        return True

    def _add_location_to_mapping(self, location_dict: dict) -> None:
        """Add location information to the mapping."""
        for literal, atoms in self._mapping.items():
            for atom in atoms:
                for symbol_schema, locs in location_dict.items():
                    if self._is_instanciation_of(atom.symbol, symbol_schema):
                        log.debug("Mapping literal %d to location %s", literal, locs)
                        # Here we could store the locations in a more structured way if needed
                        self._loc_mapping[atom.symbol] = locs

    def main(self, control: Control, files: Sequence[str]) -> None:
        """Main function to run the Explanation Director Prototype Application."""
        self._create_assumption_budget(control, self._num_of_assumptions)

        if not files:
            files = ["-"]  # nocoverage

        with ProgramBuilder(control) as bld:
            fr = ExplanationTransformer()
            parse_files(files, lambda stm: bld.add(fr.visit(stm)))

        control.register_observer(ExpObserver())
        control.ground([("base", [])])
        self._use_assumption_budget(control)

        # TODO: bring _mapping and fr._location_dict together?
        self._add_location_to_mapping(fr.get_location_dict())

        # convert assumption budget for CoreComputer
        cc = CoreComputer(control, self._assumption_budget)
        mus_generator = cc.get_multiple_minimal()
        for i, mus in enumerate(mus_generator):
            min_unsat_set = [a.literal for a in mus.assumptions]  # we ignore the sign here (since all are positive)
            print(f"Minimal core {i}:")
            core_as_str = self.core_to_str(min_unsat_set)
            print(core_as_str)
            log.debug("Minimal core %d:\n%s", i, core_as_str)


if __name__ == "__main__":  # TODO: remove this at some point
    sys.exit(int(clingo_main(ExpDirectorProto(), sys.argv[1:])))  # nocoverage

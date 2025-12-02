"""Explanation Director Prototype Application"""

import sys
from collections import defaultdict
from copy import deepcopy
from textwrap import dedent
from typing import Sequence, Tuple

import clingo.symbol as clisym
from clingexplaid.mus import CoreComputer
from clingo import ApplicationOptions, Control, SymbolicAtom, SymbolType
from clingo.application import Application, clingo_main
from clingo.ast import (
    AST,
    Aggregate,
    ASTType,
    ComparisonOperator,
    ConditionalLiteral,
    Guard,
    Location,
    ProgramBuilder,
    Rule,
    Sign,
    SymbolicTerm,
    Transformer,
    parse_files,
)
from clingo.backend import Observer
from clingo.symbol import Function, Number, String, parse_term

from explanation_director_prototype.utils.logging import get_logger

log = get_logger("main")


class ExplanationTransformer(Transformer):
    """
    Transformer to modify rules marked for explanation. Marked rules contain a literal of the form
    _explain/2 in their body."""

    def visit_Rule(self, ast: AST) -> AST:  # pylint: disable=invalid-name
        """Visit a rule AST node and transform it if it is marked for explanation."""

        def parse_location_info(location: Location) -> Tuple[String, Number, Number]:
            """Parse location information from the AST location."""
            return String(location.begin.filename), Number(location.begin.line), Number(location.begin.column)

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
                # extend arguments with location info
                # TODO:
                fun = Function(name="location", arguments=parse_location_info(ast.location))
                exp_lit.atom.symbol.arguments.append(
                    SymbolicTerm(
                        lit.location,
                        fun,
                    )
                )
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
            return new_rule
        return ast


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
            for a in ctl.symbolic_atoms.by_signature("_exp", 3):
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
        log.debug("Core literals: %s\n", core)
        for l in core:
            if l in self._mapping:
                log.debug("Explanation for assumption %s:\n", l)
                for a in self._mapping[l]:
                    result += (
                        "    "
                        + self.format_explanation_symbol(a.symbol)
                        + "\n"
                        + self.format_error_location(a.symbol)
                        + "\n"
                    )
                    log.debug(result)
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

    def format_error_location(self, symbol: clisym.Symbol) -> str:
        """Format the location of the rule creating this symbol."""
        error_location_msg = "This message was caused from rule in file {}, line {}, column {}"
        return error_location_msg.format(*[str(arg) for arg in symbol.arguments[2].arguments])

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

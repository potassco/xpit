"""
ASP Program based explainer
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Generator, List, Sequence, Union

import clingo
from clingo.ast import (
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
from clingo.symbol import parse_term
from clorm import FactBase

from xpit.definitions import ExplainablePortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit
from xpit.utils.logging import get_logger

from .base import Explainer

logger = get_logger(__name__)


class ExplainablePortionTransformer:
    """
    A transformer that finds explainable portions in a logic program
    and converts it to an explainable rule.
    """

    def __init__(self, builder: ProgramBuilder):
        self.exp_portion_ids = []
        self._builder = builder

    def register_ast(self, ast: clingo.ast.AST) -> None:
        """Registers the provided AST to the builder and the parsed rules list"""
        self._builder.add(ast)

    def process_ast_list(self, ast_list: List[clingo.ast.AST]) -> None:
        for ast in ast_list:
            if ast.ast_type == clingo.ast.ASTType.Rule:
                for new_ast in self._transform_rule(ast):
                    self.register_ast(new_ast)
            else:
                self.register_ast(ast)

    def _transform_rule(self, ast) -> Generator[clingo.ast.AST]:
        is_marked_for_explanation = False
        _explain_lit = None

        for lit in ast.body:
            if (
                lit.ast_type == ASTType.Literal
                and lit.atom.ast_type == ASTType.SymbolicAtom
                and lit.atom.symbol.ast_type == ASTType.Function
                and lit.atom.symbol.name == "_explain"
            ):
                logger.debug("Rule marked for explanation: %s", ast)
                exp_lit = deepcopy(lit)
                exp_lit.atom.symbol.name = "_exp"
                exp_lit.sign = Sign.NoSign
                _explain_lit = lit
                is_marked_for_explanation = True
                assert len(lit.atom.symbol.arguments) == 2, "_explain should have two arguments."
                if str(lit.atom.symbol.arguments[0]) in self.exp_portion_ids:
                    logger.warning("Duplicate explainable portion id found: %s", str(lit.atom.symbol.arguments[0]))
                else:
                    self.exp_portion_ids.append(str(lit.atom.symbol.arguments[0]))
                break

        if is_marked_for_explanation:
            new_rule = Rule(
                ast.location,
                Aggregate(
                    ast.location,
                    None,
                    [
                        ConditionalLiteral(ast.location, exp_lit, []),
                    ],
                    None,
                ),
                [l for l in ast.body if l != _explain_lit],
            )
            logger.debug("New rule added: %s", new_rule)
            yield new_rule
            # change the original rule into
            # head :- ...., not _exp(...).
            _explain_lit.atom.symbol.name = "_exp"

        logger.debug("Program rule: %s", ast)
        yield ast


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for explainable portions in
    tagged input input logic programs. It also binds eunits from the
    assigned budget to explainable portions.
    """

    def __init__(self, lp_files: Sequence[Union[str, Path]]) -> None:
        super().__init__()
        self.lp_files = lp_files
        self._exp_portion_ids: set[str] = None
        self._binding: defaultdict[EUnit, List[EPortion]] = defaultdict(list)

    def add_lp_file(self, lp_file: Union[str, Path]) -> None:
        """Adds an LP file to the explainer's list of LP files."""
        self.lp_files.append(lp_file)

    def add_factbase(self, factbase: FactBase) -> None:
        """Adds a Clorm FactBase to the explainer's program."""

    def _fo_transformations(self) -> None:
        if not self.control:
            raise ValueError("Unregistered explainer: control is not set.")
        ast_list: list[clingo.ast.AST] = []
        with ProgramBuilder(self.control) as bld:
            t = ExplainablePortionTransformer(builder=bld)
            parse_files([str(f) for f in self.lp_files], ast_list.append)
            t.process_ast_list(ast_list)
            self._exp_portion_ids = t.exp_portion_ids

    def setup_before_grounding(self) -> None:
        self._fo_transformations()

    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:
        if not self.control:
            raise ValueError("Unregistered explainer: control is not set.")
        logger.debug("Assigning eunit budget to explainable portions in ProgramExplainer.")
        logger.debug("ExpPortion ids: %s", self._exp_portion_ids)
        logger.debug("EUnits: %s", eunits)
        with self.control.backend() as backend:
            idx = 0
            for a in self.control.symbolic_atoms.by_signature("_exp", 2):
                if str(a.symbol.arguments[0]) not in self._exp_portion_ids:
                    continue
                exp_por = EPortion(id_=str(a.symbol.arguments[0]), exp_atom=a)
                # :- _exp(...), eunit.
                backend.add_rule(head=[], body=[a.literal, eunits[idx].assumption_lit])
                # _exp(...) :- not eunit.
                backend.add_rule(head=[a.literal], body=[-1 * eunits[idx].assumption_lit], choice=False)
                self._binding[eunits[idx]].append(exp_por)
                if idx + 1 < len(eunits):
                    idx += 1

    def get_explainable_portions(self, eunit: EUnit) -> List[EPortion]:
        return self._binding[eunit]

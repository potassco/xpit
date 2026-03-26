"""
ASP Program based explainer
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Generator, List, Optional, Sequence, Union

import clingo
import clingo.ast  # avoid LSP warnings 'Submodule ast may not be ...'
from clingo.ast import (
    Aggregate,
    ASTType,
    ConditionalLiteral,
    Function,
    Literal,
    ProgramBuilder,
    Rule,
    Sign,
    SymbolicAtom,
    SymbolicTerm,
    parse_files,
    parse_string,
)
from clorm import FactBase

from xpit.definitions import ExplanationPortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit
from xpit.definitions.define import PortionId, PortionIdFilter
from xpit.utils.logging import get_logger

from .base import Explainer

logger = get_logger(__name__)


class ExplanationPortionTransformer:
    """
    A transformer that finds explanation portions in a logic program
    and converts it to an explainable rule.
    """

    def __init__(self, builder: ProgramBuilder, fact_signatures: list[tuple[str, int]]):
        self.exp_portion_ids: PortionIdFilter = PortionIdFilter([])
        self._builder = builder
        self._fact_signatures = fact_signatures

    def register_ast(self, ast: clingo.ast.AST) -> None:
        """Registers the provided AST to the builder and the parsed rules list"""
        self._builder.add(ast)

    def process_ast_list(self, ast_list: List[clingo.ast.AST]) -> None:
        """processes a list of ASTs to transform rules marked for explanation"""
        for ast in ast_list:
            if ast.ast_type == clingo.ast.ASTType.Rule:
                for new_ast in self._transform_rule(ast):
                    self.register_ast(new_ast)
            else:
                self.register_ast(ast)

    def check_fact_signatures(self, ast_list: List[clingo.ast.AST]) -> None:
        """Check a list of ASTs to find taggable facts regarding the fact signatures"""
        for idx, ast in enumerate(ast_list):
            if (
                ast.ast_type == ASTType.Rule
                and ast.body == []
                and ast.head.ast_type == ASTType.Literal
                and (ast.head.atom.symbol.name, len(ast.head.atom.symbol.arguments)) in self._fact_signatures
            ):
                ast_list[idx] = self._tag_rule_via_signature(ast)

    def _tag_rule_via_signature(self, fact_ast: clingo.ast.AST) -> clingo.ast.AST:
        loc = fact_ast.location
        eportion_id = Function(loc, "via_sig", [fact_ast.head.atom.symbol], 0)
        eportion_msg = Function(
            loc,
            "msg",
            [
                SymbolicTerm(loc, clingo.symbol.String("Fact {} is related to the no solutions result")),
                Function(loc, "", [fact_ast.head.atom.symbol], 0),
            ],
            0,
        )
        sym_atom_explain = SymbolicAtom(Function(loc, "_explain", [eportion_id, eportion_msg], 0))
        explain_lit = Literal(loc, Sign.Negation, sym_atom_explain)
        new_rule = Rule(loc, fact_ast.head, [explain_lit])
        logger.debug("Generating new tagged rule via fact signature: %s", new_rule)
        return new_rule

    def _transform_rule(self, ast: clingo.ast.AST) -> Generator[clingo.ast.AST]:
        """transforms a rule AST into 2 rules if it is marked for explanation"""

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
                assert len(lit.atom.symbol.arguments) == 2, "_explain should have two arguments."

                tag_id = PortionId.from_ast(lit.atom.symbol.arguments[0])
                if self.exp_portion_ids.allows(tag_id):
                    logger.warning("Duplicate explainable portion id found: %s", str(lit.atom.symbol.arguments[0]))
                else:
                    self.exp_portion_ids.append(tag_id)

                # create new rule
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
                    [l for l in ast.body if l != lit],
                )
                logger.debug("New rule added: %s", new_rule)
                yield new_rule
                # change the original rule into
                # head :- ...., not _exp(...).
                lit.atom.symbol.name = "_exp"
                break

        logger.debug("Program rule: %s", ast)
        yield ast


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for explanation portions in
    tagged input input logic programs. It also binds eunits from the
    assigned budget to explanation portions.
    """

    def __init__(
        self,
        lp_files: Optional[Sequence[Union[str, Path]]] = None,
        lp_strings: Optional[Sequence[str]] = None,
        fact_signatures: Optional[Sequence[tuple[str, int]]] = None,
    ) -> None:
        """initializes the ProgramExplainer with given LP files."""
        super().__init__()
        self.lp_files = list(lp_files) if lp_files is not None else []
        self.lp_strings = list(lp_strings) if lp_strings is not None else []
        self.fact_signatures = list(fact_signatures) if fact_signatures is not None else []
        self._exp_portion_ids: PortionIdFilter = PortionIdFilter([])
        self._binding: defaultdict[EUnit, List[EPortion]] = defaultdict(list)

    def add_lp_file(self, lp_file: Union[str, Path]) -> None:
        """Adds an LP file to the explainer's list of LP files."""
        self.lp_files.append(lp_file)

    def add_lp_string(self, lp_string: str) -> None:
        """Adds an LP string to the explainer's list of LP strings."""
        self.lp_strings.append(lp_string)

    def add_factbase(self, factbase: FactBase) -> None:
        """Adds a Clorm FactBase to the explainer's program."""

    def _fo_transformations(self) -> None:
        """triggers first-order transformations on the loaded LP files"""
        if not self.control:  # nocoverage
            raise ValueError("Unregistered explainer: control is not set.")
        ast_list: list[clingo.ast.AST] = []
        with ProgramBuilder(self.control) as bld:
            t = ExplanationPortionTransformer(builder=bld, fact_signatures=self.fact_signatures)
            if self.lp_files:
                parse_files([str(f) for f in self.lp_files], ast_list.append)
            for lp_string in self.lp_strings:
                parse_string(lp_string, ast_list.append)
            t.check_fact_signatures(ast_list)
            t.process_ast_list(ast_list)
            self._exp_portion_ids = t.exp_portion_ids

    def setup_before_grounding(self) -> None:
        """sets up the explainer before grounding by performing FO transformations"""
        self._fo_transformations()

    def get_eunit_request(self) -> int:
        """request the number of eunits required for this explainer"""
        if not self.control:
            raise ValueError("Unregistered explainer: control is not set.")  # nocoverage
        logger.debug("Requesting eunit budget for ProgramExplainer.")
        return sum(
            1
            for a in self.control.symbolic_atoms.by_signature("_exp", 2)
            if self._exp_portion_ids.allows(PortionId.from_clingo_symbol(a.symbol.arguments[0]))
        )

    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:
        """assigns eunit budget to explainable portions in the program"""
        if not self.control:  # nocoverage
            raise ValueError("Unregistered explainer: control is not set.")
        logger.debug("Assigning eunit budget to explanation portions in ProgramExplainer.")
        logger.debug("EPortion ids: %s", self._exp_portion_ids)
        logger.debug("EUnits: %s", eunits)
        idx = 0
        if self.bind_filtered_out_ids and self.tag_filter is not None:
            logger.debug("Binding filtered out portion ids to a single eunit.")  # nocoverage
        with self.control.backend() as backend:
            for a in self.control.symbolic_atoms.by_signature("_exp", 2):
                # tag_id = extract_tag_id(a.symbol.arguments[0])
                tag_id_instance = PortionId.from_clingo_symbol(a.symbol.arguments[0])
                # Check if tag_id active in this expalainer and in the user-provided tag filters
                if not self._exp_portion_ids.allows(tag_id_instance):
                    continue  # nocoverage
                if self.tag_filter is not None and not self.tag_filter.allows(tag_id_instance):  # nocoverage
                    # TODO: add test case once tag filtering use cases are clear
                    # :- _exp(...).
                    if not self.bind_filtered_out_ids:
                        backend.add_rule(head=[], body=[a.literal])
                        logger.debug("added: not %s for %s", a.literal, tag_id_instance)
                    else:
                        self._bind_eunit_to_portion(backend, eunits[-1], EPortion(id_=tag_id_instance, exp_atom=a))
                    continue
                self._bind_eunit_to_portion(backend, eunits[idx], EPortion(id_=tag_id_instance, exp_atom=a))
                if idx + 1 + int(self.bind_filtered_out_ids) < len(eunits):
                    idx += 1

    def _bind_eunit_to_portion(self, backend: clingo.backend.Backend, eunit: EUnit, portion: EPortion) -> None:
        logger.debug("Binding filtered out portion id %s to eunit %s", portion.id_, eunit)
        # :- _exp(...), eunit.
        backend.add_rule(head=[], body=[portion.exp_atom.literal, eunit.assumption_lit])
        # _exp(...) :- not eunit.
        backend.add_rule(head=[portion.exp_atom.literal], body=[-1 * eunit.assumption_lit], choice=False)
        self._binding[eunit].append(portion)

    def get_explanation_portions(self, eunit: EUnit) -> List[EPortion]:
        """gets the explanation portions bound to the given eunit"""
        return self._binding[eunit]

"""
ASP Program based explainer
"""

from pathlib import Path
from typing import Sequence, Union, List
from copy import deepcopy

from clingo.ast import ASTType, Rule, Aggregate, Guard, SymbolicTerm, ConditionalLiteral, ComparisonOperator, Sign, Transformer, ProgramBuilder, parse_files
from clingo.symbol import parse_term

from clorm import FactBase

from xpit import director

from .base import Explainer

class ExpPortionTransformer(Transformer):
    """
    A transformer that finds explainable portions in a logic program
    and converts it to an explainable rule.
    """

    def __init__(self):
        self.exp_portion_ids = []

    def visit_Rule(self, ast):
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
                self.exp_portion_ids.append(str(lit.atom.symbol.arguments[0]))
                print("Explainable portion in rule", ast)
                break

        if is_marked_for_explanation:
            new_rule = Rule(
                ast.location,
                Aggregate(
                    ast.location,
                    Guard(
                        ComparisonOperator.LessEqual,
                        SymbolicTerm(ast.location, parse_term("1")),
                    ),
                    [
                        ConditionalLiteral(ast.location, ast.head, []),
                        ConditionalLiteral(ast.location, exp_lit, []),
                    ],
                    Guard(
                        ComparisonOperator.LessEqual,
                        SymbolicTerm(ast.location, parse_term("1")),
                    ),
                ),
                ast.body,
            )
            return new_rule
        return ast


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for explainable portions in
    tagged input input logic programs. It also binds eunits from the
    assigned budget to explainable portions.
    """

    def __init__(
        self, director: director.ExpDirector, lp_files: Sequence[Union[str, Path]]
    ) -> None:
        super().__init__(director)
        self.lp_files = lp_files
        self._exp_portion_ids: set[str] = None
        self._binding: Dict[director.director.EUnit, List[director.director.ExpPortion]] = {}

    def add_lp_files(self, lp_files: Union[str, Path]) -> None:
        self.lp_files.extend(lp_files)

    def add_factbase(self, factbase: FactBase) -> None:
        pass

    def _fo_transformations(self) -> int:
        with ProgramBuilder(self.control) as bld:
            t = ExpPortionTransformer()
            parse_files([str(f) for f in self.lp_files], lambda stm: bld.add(t.visit(stm)))
            self._exp_portion_ids = set(t.exp_portion_ids)
        return len(t.exp_portion_ids)

    def setup_before_grounding(self) -> int:
        return self._fo_transformations()

    def assign_eunit_budget(self, eunits: List[director.director.EUnit]) -> None:
        print("ExpPortion ids:", self._exp_portion_ids)
        print("EUnits:", eunits)
        with self.control.backend() as backend:
            idx = 0
            for a in self.control.symbolic_atoms.by_signature("_exp",2):
                if str(a.symbol.arguments[0]) not in self._exp_portion_ids:
                    continue
                exp_por = director.director.ExpPortion(id_=a.symbol.arguments[0], exp_atom=a)
                print(exp_por)
                backend.add_rule(head=[], body=[a.literal, eunits[idx].assumption_literal])
                backend.add_rule(head=[a.literal], body=[-1*eunits[idx].assumption_literal], choice=False)
                if eunits[idx] in self._binding:
                    self._binding[eunits[idx]].append(exp_por)
                else:
                    self._binding[eunits[idx]] = [exp_por]
                if idx+1 < len(eunits):
                    idx += 1

    def get_exp_portions(self, eunit: director.director.EUnit) -> List[director.director.ExpPortion]:
        if eunit not in self._binding:
            return []
        else:
            return self._binding[eunit]

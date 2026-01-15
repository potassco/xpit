"""
ASP Program based explainer
"""

from pathlib import Path
from typing import Sequence, Union, List, Dict
from copy import deepcopy

from clingo.ast import ASTType, Rule, Aggregate, Guard, SymbolicTerm, ConditionalLiteral, ComparisonOperator, Sign, Transformer, ProgramBuilder, parse_files
from clingo.symbol import parse_term

from clorm import FactBase

from xpit import director

from .base import Explainer
from ..definitions import ExplanationUnit as EUnit
from ..definitions import ExplainablePortion as EPortion

class ExplainablePortionTransformer(Transformer):
    """
    A transformer that finds explainable portions in a logic program
    and converts it to an explainable rule.
    """

    def __init__(self, builder: ProgramBuilder):
        self.exp_portion_ids = []
        self.builder = builder

    def visit_Rule(self, ast):
        is_marked_for_explanation = False
        _explain_lit = None

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
                _explain_lit = lit
                is_marked_for_explanation = True
                self.exp_portion_ids.append(str(lit.atom.symbol.arguments[0]))
                # print("Explainable portion in rule", ast)
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
            print(new_rule)
            self.builder.add(new_rule)
            # change the original rule into
            # head :- ...., not _exp(...).
            _explain_lit.atom.symbol.name="_exp"
            # return new_rule

        print("Program rule:", ast)
        return ast


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for explainable portions in
    tagged input input logic programs. It also binds eunits from the
    assigned budget to explainable portions.
    """

    def __init__(
        self, director: director.ExplanationDirector, lp_files: Sequence[Union[str, Path]]
    ) -> None:
        super().__init__(director)
        self.lp_files = lp_files
        self._exp_portion_ids: set[str] = None
        self._binding: Dict[EUnit, List[EPortion]] = {}

    def add_lp_files(self, lp_files: Union[str, Path]) -> None:
        self.lp_files.extend(lp_files)

    def add_factbase(self, factbase: FactBase) -> None:
        pass

    def _fo_transformations(self) -> int:
        with ProgramBuilder(self.control) as bld:
            t = ExplainablePortionTransformer(builder=bld)
            parse_files([str(f) for f in self.lp_files], lambda stm: bld.add(t.visit(stm)))
            self._exp_portion_ids = set(t.exp_portion_ids)
        return len(t.exp_portion_ids)

    def setup_before_grounding(self) -> int:
        return self._fo_transformations()

    def assign_eunit_budget(self, eunits: List[EUnit]) -> None:
        print("~"*40)
        print("Program-based explainer")
        print("ExpPortion ids:", self._exp_portion_ids)
        print("EUnits:", eunits)
        with self.control.backend() as backend:
            idx = 0
            for a in self.control.symbolic_atoms.by_signature("_exp",2):
                # print("ground exp atom",a.symbol)
                if str(a.symbol.arguments[0]) not in self._exp_portion_ids:
                    continue
                exp_por = EPortion(id_=str(a.symbol.arguments[0]), exp_atom=a)
                # print(exp_por)
                # :- _exp(...), eunit.
                backend.add_rule(head=[], body=[a.literal, eunits[idx].assumption_lit])
                # _exp(...) :- not eunit.
                backend.add_rule(head=[a.literal], body=[-1*eunits[idx].assumption_lit], choice=False)
                if eunits[idx] in self._binding:
                    self._binding[eunits[idx]].append(exp_por)
                else:
                    self._binding[eunits[idx]] = [exp_por]
                if idx+1 < len(eunits):
                    idx += 1

    def get_explainable_portions(self, eunit: EUnit) -> List[EPortion]:
        if eunit not in self._binding:
            return []
        else:
            return self._binding[eunit]

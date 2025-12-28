"""
ASP Program based explainer
"""

from pathlib import Path
from typing import Sequence, Union

from .base import Explainer
from ..director import ExpDirector

import clingo
from clorm import FactBase


class ExpPortionTransformer(Transformer):
    """
    A transformer that finds explainable portions in a logic program
    and converts it to an explainable rule.
    """

    def __init__(self):
        self.explainable_portion_ids = []

    def visit_Rule(self, ast):
        is_marked_for_explanation = False

        for lit in ast.body:
            if (lit.ast_type == ASTType.Literal and
               lit.atom.ast_type == ASTType.SymbolicAtom and
               lit.atom.symbol.ast_type == ASTType.Function and
                    lit.atom.symbol.name == "_explain"):
                exp_lit = deepcopy(lit)
                exp_lit.atom.symbol.name = "_exp"
                exp_lit.sign = Sign.NoSign
                is_marked_for_explanation =True
                self.is_marked_for_explanation.append(str(lit.atom.symbol.arguments[0]))
                break

        if  is_marked_for_explanation:
            new_rule = Rule(ast.location,
                            Aggregate(ast.location,
                                      Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1"))),
                                      [ConditionalLiteral(ast.location, ast.head, []),
                                       ConditionalLiteral(ast.location, exp_lit, [])],
                                      Guard(ComparisonOperator.LessEqual, SymbolicTerm(ast.location, parse_term("1")))),
                            ast.body)
            return new_rule
        return ast


class ProgramExplainer(Explainer):
    """
    Program based explainer checks for explainable portions in 
    tagged input input logic programs. It also binds eunits from the
    assigned budget to explainable portions.
    """

    def __init__(self, director: ExpDirector, lp_files: Sequence[Union[str,Path]]) -> None:
        super().__init__(director)
        self.lp_files = lp_files

    def add_lp_file(self, lp_file: Union[str,Path]) -> None:
        pass

    def add_factbase(self, factbase: FactBase) -> None:
        pass

    def _fo_transformations(self):
        with ProgramBuilder(self.control) as bld:
            t = ExpPortionTransformer()
            parse_files(self.lp_files, lambda stm: bld.add(t.visit(stm)))


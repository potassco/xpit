from typing import List
import math

import clingo
from clingo.symbol import Function

from clingexplaid.mus import CoreComputer
from clingexplaid.mus.explorers import ExplorerPowerset

# from ..explainer import Explainer
import xpit.explainer as explainer
from ..definitions import ExplanationUnit as EUnit
from ..definitions import ExplainablePortion as EPortion


class ExplanationDirector:
    """
    Explanation Director class that manages explainer modules and allocates an eunit budget.
    """

    def __init__(self, control: clingo.Control, maximum_number_of_eunits: int) -> None:
        self.control = control
        self.maximum_number_of_eunits = maximum_number_of_eunits
        self.explainers: List[explainer.Explainer] = []
        self.eunits: List[EUnit] = []

    def register_explainer(self, explainer: explainer.Explainer) -> None:
        self.explainers.append(explainer)

    def setup_before_grounding(self) -> None:
        for exp in self.explainers:
            exp.setup_before_grounding()

    def _find_eunit_for_assumption_literal(self, assumption_lit: int) -> EUnit:
        for eunit in self.eunits:
            if eunit.assumption_lit == assumption_lit:
                return eunit

    def _create_eunits(self) -> None:
        with self.control.backend() as backend:
            for i in range(self.maximum_number_of_eunits):
                sym = Function("_eunit" +  str(i+1))
                atm = backend.add_atom(sym)
                self.eunits.append(EUnit(assumption_lit=atm))
                backend.add_rule(head=[atm], choice=True)

    def _distribute_eunits_equally(self) -> List[int]:
        # first ensure at least one eunit is reserved for each explainer
        dist = [1] * len(self.explainers)
        rest = self.maximum_number_of_eunits - len(self.explainers)
        if rest < 0:
            return dist
        slice_ = math.ceil(rest / len(self.explainers))
        for idx in range(len(self.explainers)):
            if rest >= slice_:
                dist[idx] += slice_
                rest -= slice_
            else:
                dist[idx] += rest
        return dist

    def setup_before_solving(self) -> None:
        self._create_eunits()
        distribution = self._distribute_eunits_equally()
        start = 0
        for idx, exp in enumerate(self.explainers):
            exp.assign_eunit_budget(self.eunits[start:start+distribution[idx]])
            start += distribution[idx]

    def compute_minimal_core_eunits(self):
        cc = CoreComputer(self.control, [eu.assumption_lit for eu in self.eunits], ExplorerPowerset)
        mus_generator = cc.get_multiple_minimal()
        for mus in mus_generator:
            minimal_core_eunits = [self._find_eunit_for_assumption_literal(a.literal) for a in mus.assumptions]
            yield minimal_core_eunits

    def compute_explanation(self, core: List[EUnit]) -> List[EPortion]:
        explanation = []
        for eu in core:
            for exp in self.explainers:
                exp_portions = exp.get_explainable_portions(eu)
                if exp_portions:
                    explanation.extend(exp_portions)
                    break
        return explanation

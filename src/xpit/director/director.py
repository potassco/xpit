"""Director module managing explainers and eunit budget allocation."""

from typing import Generator, List

import clingo
from clingexplaid.mus import CoreComputer
from clingexplaid.mus.explorers import Explorer, ExplorerAsp, ExplorerPowerset
from clingo.symbol import Function

from xpit.definitions import ExplainablePortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit
from xpit.explainer.base import Explainer
from xpit.utils.logging import get_logger

logger = get_logger(__name__)


class ExplanationDirector:
    """
    Explanation Director class that manages explainer modules and allocates an eunit budget.
    """

    def __init__(self, control: clingo.Control, maximum_number_of_eunits: int, core_explorer: str = "powerset") -> None:
        self.control = control
        if maximum_number_of_eunits < 1:
            raise ValueError("Maximum number of eunits must be at least 1.")
        self.maximum_number_of_eunits = maximum_number_of_eunits
        self.explainers: List[Explainer] = []
        self.eunits: List[EUnit] = []
        self._core_comp_explorer: type[Explorer]
        if core_explorer.lower() == "asp":  # nocoverage
            self._core_comp_explorer = ExplorerAsp
        elif core_explorer.lower() == "powerset":
            self._core_comp_explorer = ExplorerPowerset
        else:
            raise ValueError(f"Unknown core explorer: {core_explorer}")  # nocoverage

    def register_explainer(self, explainer: Explainer) -> None:
        """registers an explainer module with the director"""
        if len(self.explainers) == self.maximum_number_of_eunits:
            raise ValueError("Number of registered explainers exceeds maximum number of eunits.")
        self.explainers.append(explainer)
        explainer.set_control(self.control)

    def setup_before_grounding(self) -> None:
        """sets up all registered explainers before grounding"""
        for exp in self.explainers:
            exp.setup_before_grounding()

    def _find_eunit_for_assumption_literal(self, assumption_lit: int) -> EUnit:
        """finds the EUnit corresponding to the given assumption literal"""
        for eunit in self.eunits:
            if eunit.assumption_lit == assumption_lit:
                return eunit
        raise ValueError(f"No EUnit found for assumption literal: {assumption_lit}")  # nocoverage

    def _create_eunits(self) -> None:
        """creates eunits in the clingo control backend"""
        with self.control.backend() as backend:
            for i in range(self.maximum_number_of_eunits):
                sym = Function("_eunit" + str(i + 1))
                atm = backend.add_atom(sym)
                self.eunits.append(EUnit(assumption_lit=atm))
                backend.add_rule(head=[atm], choice=True)

    def _distribute_eunits_equally(self) -> List[int]:
        """distributes eunits equally among registered explainers"""
        mod_rest = self.maximum_number_of_eunits % len(self.explainers)
        floor = self.maximum_number_of_eunits // len(self.explainers)
        return [floor + (1 if i < mod_rest else 0) for i in range(len(self.explainers))]

    def setup_before_solving(self) -> None:
        """sets up the director and assigns eunit budgets to explainers before solving"""
        self._create_eunits()
        distribution = self._distribute_eunits_equally()
        start = 0
        for idx, exp in enumerate(self.explainers):
            exp.assign_eunit_budget(self.eunits[start : start + distribution[idx]])
            start += distribution[idx]

    def compute_minimal_core_eunits(self) -> Generator[List[EUnit]]:
        """computes minimal core eunits using clingexplaid's CoreComputer"""
        cc = CoreComputer(self.control, [eu.assumption_lit for eu in self.eunits], self._core_comp_explorer)
        mus_generator = cc.get_multiple_minimal()
        for mus in mus_generator:
            minimal_core_eunits = [self._find_eunit_for_assumption_literal(a.literal) for a in mus.assumptions]
            yield minimal_core_eunits

    def compute_explanation(self, core: List[EUnit]) -> List[EPortion]:
        """computes the explanation for a given core of eunits"""
        explanation = []
        for eu in core:
            for exp in self.explainers:
                exp_portions = exp.get_explainable_portions(eu)
                if exp_portions:
                    explanation.extend(exp_portions)
                    break
        return explanation

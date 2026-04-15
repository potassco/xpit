"""Director module managing explainers and eunit budget allocation."""

from enum import Enum
from typing import Generator, List, Optional, Sequence

import clingo
from clingexplaid.mus import CoreComputer
from clingexplaid.mus.explorers import Explorer, ExplorerAsp, ExplorerPowerset
from clingo.symbol import Function

from xpit.definitions import ExplanationPortion as EPortion
from xpit.definitions import ExplanationUnit as EUnit
from xpit.explainer.base import Explainer
from xpit.utils.logging import get_logger

logger = get_logger(__name__)


ExplorerMethod = Enum("ExplorerMethod", {"ASP": "asp", "POWERSET": "powerset"})

DistributionMethod = Enum("DistributionMethod", {"EQUAL": "equal", "BY_REQUEST": "by_request"})


class ExplanationDirector:
    """
    Explanation Director class that manages explainer modules and allocates an eunit budget.
    """

    def __init__(
        self,
        control: clingo.Control,
        maximum_number_of_eunits: Optional[int] = None,
    ) -> None:
        self.control = control
        if maximum_number_of_eunits is not None and maximum_number_of_eunits < 1:
            raise ValueError("Maximum number of eunits must be at least 1.")
        self.eunit_auto = maximum_number_of_eunits is None
        self.maximum_number_of_eunits = maximum_number_of_eunits or 0
        self.explainers: List[Explainer] = []
        self.eunits: List[EUnit] = []

    def register_explainer(self, explainer: Explainer) -> None:
        """registers an explainer module with the director"""
        if not self.eunit_auto and len(self.explainers) == self.maximum_number_of_eunits:
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

    def _distribute_eunits_by_request(self) -> List[int]:
        """requests eunit budgets from explainers and distributes accordingly"""
        requests = [exp.get_eunit_request() for exp in self.explainers]
        total_requested = sum(requests)
        if total_requested <= self.maximum_number_of_eunits:
            return requests
        # Scale down requests proportionally
        scaled = [max(1, (req * self.maximum_number_of_eunits) // total_requested) for req in requests]
        # Adjust in case of rounding issues
        add_value = 0
        if sum(scaled) < self.maximum_number_of_eunits:
            add_value = 1
        elif sum(scaled) > self.maximum_number_of_eunits:
            add_value = -1
        while sum(scaled) != self.maximum_number_of_eunits:  # we need the while loop because of the max(1, ...) above
            for i, _ in enumerate(scaled):
                if scaled[i] > 1 or add_value == 1:
                    scaled[i] += add_value
                    if sum(scaled) == self.maximum_number_of_eunits:
                        break
        logger.debug("EUnit requests: %s", requests)
        logger.debug("Scaled EUnit distribution: %s", scaled)
        return scaled

    def setup_before_solving(self, dist_method: Optional[DistributionMethod] = None) -> None:
        """sets up the director and assigns eunit budgets to explainers before solving
        Args:
            dist_method (DistributionMethod): Method for distributing eunits among explainers.
        """
        if self.eunit_auto:
            if dist_method is not None:  # nocoverage
                logger.warning("EUnit auto mode is enabled, but a distribution method is given. Ignoring given method.")
            distribution = [exp.get_eunit_request() for exp in self.explainers]
            total_requested = sum(distribution)
            logger.debug(
                "%s EUnits requested from explainers; set maximum_number_of_eunits accordingly", total_requested
            )
            self.maximum_number_of_eunits = total_requested

        elif dist_method is None or dist_method == DistributionMethod.EQUAL:  # default case
            distribution = self._distribute_eunits_equally()
        elif dist_method == DistributionMethod.BY_REQUEST:  # nocoverage
            distribution = self._distribute_eunits_by_request()  # TODO: add tag_filters to by_request method as well
        else:
            raise ValueError(f"Unknown distribution method: {dist_method}")  # nocoverage

        # create eunits and assign to explainers
        self._create_eunits()
        logger.debug("EUnit distribution among explainers: %s", distribution)
        start = 0
        for idx, exp in enumerate(self.explainers):
            exp.assign_eunit_budget(self.eunits[start : start + distribution[idx]])
            start += distribution[idx]

    def compute_one_minimal_core_eunits(self) -> List[EUnit] | None:
        """computes a singe minimal core eunits via shrinking the core got from clingo"""
        mus: List[EUnit] | None = None

        def shrink_core(core: Sequence[int]) -> None:
            nonlocal mus
            if core == []:
                mus = []
            else:
                minimal_assumptions = cc.shrink(core)
                mus = [self._find_eunit_for_assumption_literal(a.literal) for a in minimal_assumptions.assumptions]

        cc = CoreComputer(self.control, [eu.assumption_lit for eu in self.eunits])
        self.control.solve(
            assumptions=[eu.assumption_lit for eu in self.eunits], on_core=shrink_core
        )
        if mus is None:
            logger.warning("No core is computed, check whether the input program is inconsistent or not.")  # nocoverage
        return mus

    def compute_all_minimal_core_eunits(
        self, core_explorer: ExplorerMethod = ExplorerMethod.POWERSET
    ) -> Generator[List[EUnit]]:
        """computes minimal core eunits using clingexplaid's CoreComputer"""
        core_comp_explorer: type[Explorer]
        if core_explorer == ExplorerMethod.ASP:  # nocoverage
            core_comp_explorer = ExplorerAsp
        elif core_explorer == ExplorerMethod.POWERSET:
            core_comp_explorer = ExplorerPowerset
        else:
            raise ValueError(f"Unknown core explorer: {core_explorer}")  # nocoverage
        cc = CoreComputer(self.control, [eu.assumption_lit for eu in self.eunits], core_comp_explorer)
        mus_generator = cc.get_multiple_minimal()
        for mus in mus_generator:
            minimal_core_eunits = [self._find_eunit_for_assumption_literal(a.literal) for a in mus.assumptions]
            yield minimal_core_eunits

    def compute_explanation(self, core: List[EUnit]) -> List[EPortion]:
        """computes the explanation for a given core of eunits"""
        explanation = []
        for eu in core:
            for exp in self.explainers:
                exp_portions = exp.get_explanation_portions(eu)
                if exp_portions:
                    explanation.extend(exp_portions)
                    break
        return explanation

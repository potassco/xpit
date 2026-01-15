import logging
import sys

import clingo

from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer
from xpit.utils.logging import configure_logging

configure_logging(sys.stderr, logging.DEBUG, sys.stderr.isatty())

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 20)
pe_encoding = ProgramExplainer(lp_files=["eventschedule.lp"])
pe_instance = ProgramExplainer(lp_files=["art_event.lp"])

expdir.register_explainer(pe_encoding)
expdir.register_explainer(pe_instance)

expdir.setup_before_grounding()

ctl.ground([("base", [])])

expdir.setup_before_solving()

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

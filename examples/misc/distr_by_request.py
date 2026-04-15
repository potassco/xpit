"""example usage of xpit library"""

import logging
import sys

import clingo

from xpit.director import ExplanationDirector
from xpit.director.director import DistributionMethod
from xpit.explainer import ProgramExplainer
from xpit.utils.logging import configure_logging

configure_logging(sys.stderr, logging.DEBUG, sys.stderr.isatty())


ctl = clingo.Control()

PROGRAM1 = """
a(X) :- X=1..10, not _explain(r1, msg("",(X))).
:- a(X).

"""

PROGRAM2 = """
b(X) :- X=1..5, not _explain(r2, msg("",(X))).
:- b(X).
"""

expdir = ExplanationDirector(ctl, 6)
pe_enc_1 = ProgramExplainer(lp_strings=[PROGRAM1])
pe_enc_2 = ProgramExplainer(lp_strings=[PROGRAM2])

expdir.register_explainer(pe_enc_1)
expdir.register_explainer(pe_enc_2)

# pe_enc_1.add_tag_filter(tagfilter(...))
# explainer:
#   - tag_filter(r1,r2)

expdir.setup_before_grounding()  # this is supposed to clean the filter;

ctl.ground([("base", [])])
# pe_enc_1.add_tag_filter(tagfilter(...))

# explainer:
#   - tag_filter = None
expdir.setup_before_solving(dist_method=DistributionMethod.BY_REQUEST)

for core in expdir.compute_all_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

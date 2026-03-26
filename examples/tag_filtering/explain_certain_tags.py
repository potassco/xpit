"""example usage of tag filtering in the solve call"""

import logging
import sys

import clingo

from xpit.definitions.define import PortionId, PortionIdFilter
from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer
from xpit.utils.logging import configure_logging

configure_logging(sys.stderr, logging.DEBUG, sys.stderr.isatty())


PROGRAM = """
a(X) :- X=1..3, not _explain(fact(a,X), msg("",(X))).
b(X) :- X=1..3, not _explain(fact(b,X), msg("",(X))).

:- a(X), b(X), not _explain(constraint(X), msg("",())).

"""

# expdir.setup_before_solving(ids=[("r1",[2,WildCard.All,lambda x: x<1]), ("r1", [11])])
ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 10)
pe_enc_1 = ProgramExplainer(lp_strings=[PROGRAM])

expdir.register_explainer(pe_enc_1)

expdir.setup_before_grounding()

ctl.ground([("base", [])])
# expdir.setup_before_solving()

pe_enc_1.add_tag_filter(PortionIdFilter([PortionId("constraint")]))

expdir.setup_before_solving()
# expdir.setup_before_solving(tag_filters=TagIdFilter([TagId("fact", 1)]))

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

# expdir.setup_before_solving(tags=["r1"])

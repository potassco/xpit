"""example usage of tag filtering in the solve call"""

import logging
import sys

import clingo

from xpit.definitions.define import Argument, PortionId, PortionIdFilter, WildCardArgument
from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer
from xpit.utils.logging import configure_logging

configure_logging(sys.stderr, logging.DEBUG, sys.stderr.isatty())


PROGRAM = """
a(X,Y) :- X=2..5, Y=1..3, not _explain(fact(X,Y,X+Y), msg("The problem is the derivation of a({}, {})",(X,Y))).
b(X,Y) :- X=2..5, Y=1..3, not _explain(fact(X,Y), msg("The problem is the derivation of b({}, {})",(X,Y))).

:- a(X,Y), X+Y=4, b(X',Y'), X'-Y'>3, not _explain(constraint(X,Y,X',Y'), msg("combination of a({}, {}) and b({}, {}) is invalid",(X,Y,X',Y'))).
"""

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 15)
pe_enc_1 = ProgramExplainer(lp_strings=[PROGRAM])

expdir.register_explainer(pe_enc_1)

expdir.setup_before_grounding()

ctl.ground([("base", [])])
# expdir.setup_before_solving()


pe_enc_1.add_tag_filter(
    tag_filter=PortionIdFilter(
        [PortionId(name="constraint", arity=4), PortionId(name="fact", arity=3, arguments=lambda x,y,_: x+y==4),
         PortionId(name="fact", arity=2, arguments=lambda x,y: x-y>3)]
    )
)

expdir.setup_before_solving()

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

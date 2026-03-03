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
a(X) :- X=2..5, not _explain(fact("a",X), msg("The problem is the derivation of a({})",(X))).
b(X) :- X=2..5, not _explain(fact(b,(X,X)), msg("The problem is the derivation of b({})",(X))).
c(X) :- X=1..4, not _explain(fact(c(X,"c1","c2"),X), msg("The problem is the derivation of c({})",(X))).

:- a(X), b(Y), c(Z), X+Y=Z, not _explain(constraint(X,Y,Z), msg("The combination of a({}), b({}), and c({}) is invalid",(X,Y,Z))).
:- a(X), c(Z), Z+Z=X, not _explain(constraint(X,Z), msg("The combination of a({}) and c({}) is invalid",(X,Z))).
"""

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 50)
pe_enc_1 = ProgramExplainer(lp_strings=[PROGRAM])

expdir.register_explainer(pe_enc_1)

expdir.setup_before_grounding()

ctl.ground([("base", [])])
# expdir.setup_before_solving()

# This is written for explanation; in practice, you would likely do not name the PortionIds and rather define directly.
# this PortionId activates all _explain statements tagged with constraint/2.
binary_constraint_id = PortionId(name="constraint", arity=2)
# this PortionId activates all _explain statements tagged with constraint/3 where the third argument is 4.
ternary_constraint_id = PortionId(
    name="constraint", arity=3, arguments=[WildCardArgument("*"), WildCardArgument("*"), 4]
)
# this PortionId activates all _explain statements tagged with constraint/3 where the first argument is even.
even_ternary_constraint_id = PortionId(
    name="constraint",
    arity=3,
    arguments=[lambda x: isinstance(x, int) and x % 2 == 0, WildCardArgument("*"), WildCardArgument("*")],
)
# this PortionId activates all _explain statements tagged with fact/2 where the first argument is "a".
fact_a_id = PortionId(name="fact", arity=2, arguments=["a", WildCardArgument("*")])

# the next two are a little more complex:
# If a PortionId has a tuple as an argument, one must give this tuple as a list of explicitly created Arguments.
# (In contrast, above one could just write arguments=["a", WildCardArgument("*")] instead of
# arguments=[Argument("a"), Argument(WildCardArgument("*"))] which has the same meaning.
# this PortionId activates all _explain statements tagged with fact/2 where the first argument is b,
# and the second a tuple where the first value is smaller than 3.
fact_b_id = PortionId(
    name="fact",
    arity=2,
    arguments=[Argument("b"), Argument([Argument(lambda x: x < 3), Argument(WildCardArgument("*"))])],
)
# the same holds if inside the Id there is a predicate (like fact(c(X)) in the example program).
fact_c_id = PortionId(
    name="fact", arity=2, arguments=[Argument(("c", [Argument(lambda x: x < 3)])), WildCardArgument("*")]
)

expdir.setup_before_solving(
    tag_filters=PortionIdFilter(
        [binary_constraint_id, ternary_constraint_id, even_ternary_constraint_id, fact_a_id, fact_b_id, fact_c_id]
    )
)

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

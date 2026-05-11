"""example usage of tag_filtering before grounding withxpit library"""

import clingo

from xpit.definitions.define import PortionIdFilter
from xpit.director.director import ExplanationDirector
from xpit.explainer import ProgramExplainer

LP_STRING = """
a(X) :- X=1..3, not _explain(r1(X), msg("",())).
b(X) :- X=1..3, not _explain(r2(X), msg("",())).
:- a(X), b(X), not _explain(constraint, msg("",())).
"""

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 4)
pe_encoding = ProgramExplainer(
    lp_strings=[LP_STRING],
    tag_filter=PortionIdFilter(
        ["constraint", "r1/1"]
        ) # only explain rules tagged with constraint or r1, but not r2
    ) 

expdir.register_explainer(pe_encoding)

expdir.setup_before_grounding()

ctl.ground([("base", [])])

expdir.setup_before_solving()

for core in expdir.compute_all_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

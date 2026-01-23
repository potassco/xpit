"""example usage of xpit library"""  # TODO: duplicated code, example to similiar to others

import clingo

from xpit.director.director import ExplanationDirector
from xpit.explainer import ProgramExplainer

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 4)
pe_encoding = ProgramExplainer(lp_files=["test.lp"])

expdir.register_explainer(pe_encoding)

expdir.setup_before_grounding()

ctl.ground([("base", [])])

expdir.setup_before_solving()

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

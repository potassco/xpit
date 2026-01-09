import clingo

from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer

ctl = clingo.Control()

expdir = ExplanationDirector(ctl, 2)
pe_encoding = ProgramExplainer(director = expdir, lp_files = ["simple.lp"])

expdir.register_explainer(pe_encoding)

expdir.setup_before_grounding()

ctl.ground([("base",[])])

expdir.setup_before_solving()

print(pe_encoding._binding)

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

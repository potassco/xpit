import clingo

from xpit.director import ExpDirector
from xpit.explainer import ProgramExplainer

ctl = clingo.Control()

expdir = ExpDirector(ctl, 20)
pe_encoding = ProgramExplainer(director = expdir, lp_files = ["eventschedule.lp"])
pe_instance = ProgramExplainer(director = expdir, lp_files = ["art_event.lp"])

expdir.register_explainer(pe_encoding)
expdir.register_explainer(pe_instance)

expdir.setup_before_grounding()

ctl.ground([("base",[])])

expdir.setup_before_solving()

for core in expdir.compute_minimal_core_eunits():
    print("\n")
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

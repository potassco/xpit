"""example usage of xpit library"""

import sys

import clingo

from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer

ctl = clingo.Control()

if len(sys.argv) < 3:
    print("Usage: python explain_ex1.py <eunits_num> <lp_file1> [<lp_file2> ...]")
    sys.exit(1)

lp_files = sys.argv[2:]
eunit_num = int(sys.argv[1])

expdir = ExplanationDirector(ctl, eunit_num)
pe_encoding = ProgramExplainer(lp_files=lp_files)

expdir.register_explainer(pe_encoding)

expdir.setup_before_grounding()

ctl.ground([("base", [])])

expdir.setup_before_solving()

for core in expdir.compute_minimal_core_eunits():
    print("Explanation for lp_files:", lp_files)
    print("Number of eunits:", eunit_num)
    print("Minimal core eunits:", core)
    print("Explanation atoms:")
    for exp_por in expdir.compute_explanation(core):
        print(exp_por.exp_atom.symbol)

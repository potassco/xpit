import sys
import logging

import click
import clingo

from xpit.director import ExplanationDirector
from xpit.director import ExplorerMethod 
from xpit.explainer import ProgramExplainer
from xpit.definitions.define import PortionId, PortionIdFilter
from xpit.utils.logging import configure_logging, get_logger

configure_logging(sys.stdout, logging.DEBUG, True)
logger = get_logger(__name__)

@click.command()
@click.option(
    "--max-eunit-num",
    type=int,
    help=(
        "Maximum number of explanation units to be created by the xpit director. "
        "For automatic calculation of this number, do not set this option. (default: None)"
    ),
    default=None,
    required=False,
)
@click.option(
    "--fact-sig",
    type=str,
    help="Fact signature to be tagged as xpit explanation portion (can be multiple and default: [])",
    default=[],
    required=False,
    multiple=True,
)
@click.option(
    "--number_of_explanations",
    "-n",
    type=int,
    default=1,
    help="Number of explanations to find. 0 means find all explanations. (default: 1)",
)
@click.argument(
    "lp_program_files",
    type=click.Path(exists=True),
    nargs=-1,
)
def run_explanation(max_eunit_num, fact_sig, number_of_explanations, lp_program_files):
    fact_signatures = []
    for sig in fact_sig:
        (n, a) = sig.split("/")
        fact_signatures.append((n, int(a)))
    logger.info("Fact signatures: %s", fact_signatures)

    ctl = clingo.Control()

    expdir = ExplanationDirector(ctl, max_eunit_num)
    pe_encoding = ProgramExplainer(lp_files=lp_program_files, fact_signatures=fact_signatures)

    logger.info("Explanation for lp_files: %s", lp_program_files)
    logger.info("Number of eunits: %s", max_eunit_num)

    expdir.register_explainer(pe_encoding)
    expdir.setup_before_grounding()
    ctl.ground([("base", [])])

    # create id filters

    same_num_in_row_id= PortionId(
            name = "same_num_in_row",
            arity = 4,
            # arguments = lambda y,v,x,xp: y in [4,5],
            arguments = lambda y,v,x,xp: v == 2,
    )

    same_num_in_column_id= PortionId(
            name = "same_num_in_column",
            arity = 4,
            # arguments = lambda x,v,y,yp: x in [5,6],
            arguments = lambda x,v,y,yp: v == 2,
    )

    same_num_in_subgrid_id= PortionId(
            name = "same_num_in_subgrid",
            arity = 6,
            # arguments = lambda s,v,x,y,xp,yp: s in [4],
            arguments = lambda s,v,x,y,xp,yp: v == 2,
    )

    query_id = PortionId(
            name = "query",
            arity = 0
    )

    pe_encoding.add_tag_filter(tag_filter=PortionIdFilter([same_num_in_row_id, same_num_in_column_id, same_num_in_subgrid_id, query_id]))

    expdir.setup_before_solving()

    idx = 0
    if number_of_explanations == 1:
        core = expdir.compute_one_minimal_core_eunits()
        if core is not None:
            idx += 1
            print("Explanation #%d" % (idx))
            print("Minimal core eunits: %s" % (core))
            for exp_por in expdir.compute_explanation(core):
                print(exp_por.get_message())
    else:
        for core in expdir.compute_all_minimal_core_eunits(ExplorerMethod.ASP):
            idx += 1
            if number_of_explanations > 0 and idx > number_of_explanations:
                return
            print("Explanation #%d" % (idx))
            print("Minimal core eunits: %s" % (core))
            for exp_por in expdir.compute_explanation(core):
                print(exp_por.get_message())


if __name__ == "__main__":
    run_explanation()

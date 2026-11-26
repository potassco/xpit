# pylint: skip-file
import logging
import sys

import click
import clingo

from xpit.definitions.define import PortionId, PortionIdFilter
from xpit.director import ExplanationDirector
from xpit.explainer import ProgramExplainer
from xpit.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@click.command(
    help=(
        """
        xpit script for the sudoku example. (sudoku.lp + extreme_instance.lp)

        \b
        Explore which clues justify values at (4,5).
        Use -n 0 to find all explanations.
        Use --fact-sig initial/3 to explain clues individually.
        """
    )
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity. (default: info)",
)
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
def run_explanation(log_level, max_eunit_num, fact_sig, number_of_explanations, lp_program_files):
    configure_logging(sys.stdout, getattr(logging, log_level), True)

    fact_signatures = []
    for sig in fact_sig:
        (n, a) = sig.split("/")
        fact_signatures.append((n, int(a)))
    logger.info("Fact signatures: %s", fact_signatures)

    ctl = clingo.Control()

    expdir = ExplanationDirector(ctl, max_eunit_num)
    pe_encoding = ProgramExplainer(lp_files=lp_program_files, fact_signatures=fact_signatures)

    emptycell_encoding = ProgramExplainer(lp_files=["empty_cells.lp"])

    logger.info("Explanation for lp_files: %s", lp_program_files)
    logger.info("Number of eunits: %s", max_eunit_num)

    expdir.register_explainer(pe_encoding)
    expdir.register_explainer(emptycell_encoding)
    expdir.setup_before_grounding()
    ctl.ground([("base", [])])

    # create id filters

    query_id = PortionId(name="query", arity=0)

    initial_id = PortionId(name="via_sig", arity=1, arguments=lambda t: (lambda n, a: n == "initial")(*t))

    place_id = PortionId(
        name="place",
        arity=3,
        # arguments = lambda x,y,v: True
        # arguments = lambda x,y,v: (x,y) in [(4,5), (6,6), (5,6),]
        arguments=lambda x, y, v: (x, y)
        in [
            (4, 5),
        ],
    )

    pe_encoding.add_tag_filter(PortionIdFilter([initial_id, query_id]))

    emptycell_encoding.set_bind_filtered_out_ids(True)
    emptycell_encoding.add_tag_filter(
        tag_filter=PortionIdFilter(
            [
                place_id,
            ]
        )
    )

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
        for core in expdir.compute_all_minimal_core_eunits():
            idx += 1
            if number_of_explanations > 0 and idx > number_of_explanations:
                return
            print("Explanation #%d" % (idx))
            print("Minimal core eunits: %s" % (core))
            for exp_por in expdir.compute_explanation(core):
                print(exp_por.get_message())


if __name__ == "__main__":
    run_explanation()

"""
The main entry point for the application.
"""

import sys

from clingo.application import clingo_main

from .exp_director import ExpDirectorProto
from .utils.logging import configure_logging, get_logger
from .utils.parser import get_parser


def main() -> None:
    """
    Run the main function.
    """
    parser = get_parser()
    args, clingo_args = parser.parse_known_args()
    configure_logging(sys.stderr, args.log, sys.stderr.isatty())

    if hasattr(args, "log"):
        delattr(args, "log")
    log = get_logger("main")
    log.info("info")
    log.warning("warning")
    log.debug("debug")
    log.error("error")

    # TODO: how does this main function work?
    # read all input arguments
    input_args = vars(args)
    log.debug(f"Input arguments: {input_args}")

    # Call the clingo main function with the ExpDirectorProto class and input arguments
    sys.exit(int(clingo_main(ExpDirectorProto(), clingo_args + [f"--assumpt-num={args.assumpt_num}"])))


if __name__ == "__main__":
    main()

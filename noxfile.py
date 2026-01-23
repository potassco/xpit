import os

import nox

nox.options.sessions = "lint_pylint", "typecheck", "test"

EDITABLE_TESTS = True
PYTHON_VERSIONS = None
if "GITHUB_ACTIONS" in os.environ:
    PYTHON_VERSIONS = ["3.13"]
    EDITABLE_TESTS = False


@nox.session
def dev(session):
    """
    Create a development environment in editable mode.

    Activate it by running `source .nox/dev/bin/activate`.
    """
    session.install("-e", ".[dev]")


@nox.session
def lint_pylint(session):
    """
    Run pylint.
    """
    session.install("-e", ".[lint_pylint]", "-e", ".[test]")
    session.run("pylint", "--disable=W0511", "xpit", "tests")


@nox.session
def typecheck(session):
    """
    Typecheck the code using mypy.
    """
    session.install("-e", ".[typecheck]")
    session.run("mypy", "--strict", "-p", "xpit", "-p", "tests")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """
    Run the tests.

    Accepts an additional arguments which are passed to the pytest module.
    This can for example be used to selectively run test cases.
    """
    session.install("-e", ".[test]")
    if session.posargs:
        session.run("pytest", *session.posargs, "-v")
    else:
        session.run("pytest", "-v")

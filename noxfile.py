import nox


@nox.session(python=["3.12"])
def tests(session) -> None:
    session.install("hypothesis")
    session.install(".")
    session.run("python", "-m", "unittest", "discover", "tests")


@nox.session(python=["3.12"])
def lint(session) -> None:
    session.install("ruff")
    session.run("ruff", "check", "src", "tests")


@nox.session(python=["3.12"])
def type_check(session) -> None:
    session.install("mypy", "pyright", "hypothesis", "nox")
    session.run("pyright")

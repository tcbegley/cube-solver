import nox

SOURCES = ["twophase", "setup.py"]


@nox.session()
def lint(session):
    session.install("black", "isort", "flake8")
    session.run("black", "--check", *SOURCES)
    session.run("isort", "--check", "--recursive", *SOURCES)
    session.run("flake8", *SOURCES)

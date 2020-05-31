import nox

SOURCES = ["twophase", "noxfile.py"]


@nox.session()
def lint(session):
    """Lint python source"""
    session.install("black", "isort", "flake8")
    session.run("black", "--check", *SOURCES)
    session.run("isort", "--check", "--recursive", *SOURCES)
    session.run("flake8", *SOURCES)


@nox.session()
def build(session):
    """Check and build"""
    session.install("poetry")
    env = {"VIRTUAL_ENV": session.virtualenv.location}
    session.run("poetry", "check", env=env, external=True)
    session.run("poetry", "build", env=env, external=True)

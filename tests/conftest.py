import os

import pytest

from twophase.tables import delete_tables, make_or_load_tables


@pytest.fixture(scope="session")
def tables(tmp_path_factory):
    if "REMAKE_TABLES" in os.environ:
        # In CI we want to remake tables from scratch, but when testing locally that
        # can be annoying since it takes a little while
        path = tmp_path_factory.mktemp("tables") / "tables.pkl"
        yield make_or_load_tables(path)
        delete_tables(path)
    else:
        yield make_or_load_tables()

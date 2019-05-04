import pytest
from pbutils.sqla_core import init_sqla

@pytest.fixture
def sqlite_test_db_url():
    return 'sqlite:///tests/test.db'


@pytest.fixture
def eng_meta_conn(sqlite_test_db_url):
    yield init_sqla(sqlite_test_db_url)


@pytest.fixture
def tables(eng_meta_conn):
    yield import_tables(engine, meta)
    

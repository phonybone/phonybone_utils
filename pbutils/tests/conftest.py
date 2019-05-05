import pytest
from pbutils.sqla_core import init_sqla, import_tables

@pytest.fixture
def sqlite_test_db_url():
    return 'sqlite:///tests/test.db'


@pytest.fixture
def eng_meta_conn(sqlite_test_db_url):
    ''' yields a tuple: engine, meta, and connection '''
    yield init_sqla(sqlite_test_db_url)


@pytest.fixture
def tables(eng_meta_conn):
    engine, meta, conn = eng_meta_conn
    yield import_tables(engine, meta)
    

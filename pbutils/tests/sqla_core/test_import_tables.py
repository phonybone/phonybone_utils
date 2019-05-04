from sqlalchemy import Table
from pbutils.sqla_core import init_sqla, SimpleStore, table_by_name, import_tables


def test_primary_keys(sqlite_test_db_url):
    engine, meta, conn = init_sqla(sqlite_test_db_url)
    tables = import_tables(engine, meta)

    for tablename, table in tables.items():
        assert isinstance(table, Table)

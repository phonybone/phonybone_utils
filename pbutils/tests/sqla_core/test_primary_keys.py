from pbutils.sqla_core import init_sqla, SimpleStore, table_by_name, import_tables


def test_primary_keys(sqlite_test_db_url):
    engine, meta, conn = init_sqla(sqlite_test_db_url)
    tables = import_tables(engine, meta)

    account_table = table_by_name(meta, 'account')
    assert account_table is not None
    store = SimpleStore(conn, account_table)
    pks = store.primary_keys

    for pk_col in pks:
        assert pk_col.primary_key

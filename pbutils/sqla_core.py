import sqlalchemy as sa
import logging
from pbutils.streams import records
log = logging.getLogger(__name__)

meta = sa.MetaData()
engine = None


def init_sqla(db_url):
    ''' returns a connection to the db pointed at by db_url '''
    global engine
    engine = sa.create_engine(db_url)
    conn = engine.connect()
    meta.create_all(engine)
    return engine, meta, conn


def import_tables(engine, meta):
    '''
    Get all tables from a db engine.
    Return a dict: k=tablename, v=table
    '''
    meta.reflect(bind=engine)
    return meta.tables


def table_by_name(meta, tablename):
    return meta.tables.get(tablename)  # or none


def cols_of(table):
    return table.c


def colnames_of(table):
    return [col.name for col in cols_of(table)]


def col_of(table, col_name):
    ''' Mnemonic to return a column of a table '''
    return getattr(table.c, col_name)


def url_of(connection):
    return connection.engine.url


def do_stream(connection, stream):
    '''
    Execute all the statements in a stream.
    Blindly.  No safety whatsoever.  Caller's responsibilty.

    Also not guaranteed to be correct; just splits on lines ending in ';'.
    '''
    for stmt in records(stream, ";\n"):
        connection.execute(sa.text(stmt).execution_options(autocommit=False))


def get_primary_keys(table):
    return [c[1] for c in table.c.items() if c[1].primary_key]


def get_foreign_key_cols(table):
    '''
    return fk columns as dict:
    key=fk_col_name, value=(tablename, pk) tuple
    '''
    fks = {}
    for colname, col in table.c.items():
        for fk in col.foreign_keys:  # usually empty
            parent_tname, parent_cname = fk.target_fullname.split('.')
            fks[colname] = (parent_tname, parent_cname)
    return fks


class SimpleStore:
    """
    Base class that provides some convenience for (very) simple CRUD operations
    via SqlAlchemy.

    Using this class imposes a lot of restrictions, including (but not limited to):
    - no joins
    - no group by, no ordering, no limits, etc...
    """

    def __init__(self, conn, table):
        self.conn = conn
        self.table = table

    @property
    def primary_keys(self):
        ''' return list of column objects designated as primary keys  '''
        if not hasattr(self, '__primary_keys'):
            self.__primary_keys = get_primary_keys(self.table)
        return self.__primary_keys

    @property
    def foreign_keys(self):
        if not hasattr(self, '__foreign_keys'):
            self.__foreign_keys = get_foreign_key_cols(self.table)
        return self.__foreign_keys

    def insert(self, row):
        """ Insert a row (dict) into the db """
        stmt = self.table.insert().values(**row)
        result = self.conn.execute(stmt)  # auto-commits
        return result.lastrowid

    def get_pk(self, pk):
        ''' return the row for the given primary key, or None '''
        stmt = sa.select(self.table.c.values()).where(self.primary_keys[0] == pk)
        return self.conn.execute(stmt).first()  # returns None when not found

    def get(self, **where):
        """
        yield all rows (as dicts) with properties defined by **where (and, ==)
        """
        stmt = sa.select(self.table.c.values())
        for field, value in where.items():
            stmt = stmt.where(getattr(self.table.c, field) == value)
        results = self.conn.execute(stmt).fetchall()

        for row in results:
            yield dict(row.items())

    def delete(self, **where):
        """ Delete all matching rows """
        stmt = self.table.delete()
        for field, value in where.items():
            stmt = stmt.where(getattr(self.table.c, field) == value)
        return self.conn.execute(stmt)

    def update(self, pk, data):
        """ update a given row based on a (single) primary key (named 'id') """
        pk_col = self.primary_keys[0]
        stmt = self.table.update().where(pk_col == pk).values(**data)  # todo: c.id -> pks
        return self.conn.execute(stmt)

    def clear(self):
        ''' delete all assets '''
        self.conn.execute(self.table.delete())  # auto-commits

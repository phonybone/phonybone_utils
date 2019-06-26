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
    ''' Return a dict: k=tablename, v=table '''
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
    trans = connection.begin()
    try:
        for stmt in records(stream, ";\n"):
            connection.execute(sa.text(stmt))
    except sa.exc.OperationalError:
        trans.rollback()
    else:
        trans.commit()

class SimpleStore:
    """
    Base class that provides some convenience for (very) simple CRUD operations
    via SqlAlchemy.

    Using this class imposes a lot of restrictions, including (but not limited to):
    - Each table must have a single primary key named "id"
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
            self.__primary_keys = [c[1] for c in self.table.c.items() if c[1].primary_key]
        return self.__primary_keys

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

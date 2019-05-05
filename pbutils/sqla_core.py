import sqlalchemy as sa
from sqlalchemy.inspection import inspect
import logging
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
        self.primary_keys = [c[1] for c in self.table.c.items() if c[1].primary_key]

    def insert(self, row):
        """ Insert a row (dict) into the db """
        stmt = self.table.insert().values(**row)
        result = self.conn.execute(stmt)  # auto-commits
        return result.lastrowid

    def get_pk(self, pk):
        stmt = sa.select(self.table.c.values()).where(self.primary_keys == pk)
        print(f"{str(stmt)}, pk={pk}")
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
        stmt = self.table.update().where(self.table.c.id == pk).values(**data)
        return self.conn.execute(stmt)

    def clear(self):
        ''' delete all assets '''
        self.conn.execute(self.table.delete())  # auto-commits

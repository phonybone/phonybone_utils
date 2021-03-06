import sys
import os
import copy
import datetime
from contextlib import contextmanager
import sqlalchemy as sa
import multiprocessing as mp

PYTHON2 = sys.version_info[0] == 2
PYTHON3 = sys.version_info[0] == 3
assert PYTHON2 or PYTHON3

if PYTHON2:
    import md5
    import mysql.connector
    from mysql.connector.errors import Error as _MysqlError, OperationalError
elif PYTHON3:
    from hashlib import md5
    import pymysql as mysql
    from pymysql.err import OperationalError

from .dicts import hashsubset, to_dict
from .strings import ppjson, qw
from .configs import get_config

def get_mysql(host, database, user, password):
    ''' Connect to a mysql database. '''
    if PYTHON2:
        return mysql.connector.connect(host=host, database=database, user=user, password=password)
    elif PYTHON3:
        return mysql.connect(host=host, database=database, user=user, password=password)

def get_mysql_from_config(config, section):
    mysql_args = hashsubset(to_dict(config, section), 'host', 'database', 'user', 'password')
    return get_mysql(**mysql_args)

def get_mysql_cmdline(opts, connect=False):
    ''' 
    Connect to a mysql database based on cmd-line options.  
    Also looks in ~/.my.cnf for missing values, args in opts have precedence.
    opts is a Namespace object as returned by argparse.parse_args()
    '''
    conn_args = {}
    for arg in ['host', 'database', 'user', 'password']:
        if hasattr(opts, arg):
            conn_args[arg] = getattr(opts, arg)

    config = get_config(os.path.join(os.environ.get('HOME'), '.my.cnf'))
    if config.has_section('mysql'):
        if 'user' not in conn_args or not conn_args['user']:
            try:
                conn_args['user'] = config.get('mysql', 'user')
            except Exception as e:
                pass
        if 'password' not in conn_args or not conn_args['password']:
            if config.has_option('mysql', 'password'):
                conn_args['password'] = config.get('mysql', 'password')

    if connect:
        return get_mysql(**conn_args)
    else:
        return conn_args

def get_database(dbh):
    ''' return the name of the database to which we're connected as a str() '''
    if PYTHON2:
        return dbh.database
    elif PYTHON3:
        return dbh.db.decode()
    

def get_tables(dbh, db_name=None):
    ''' return a list of tablenames for a given database '''
    if db_name is None:
        db_name = get_database(dbh)

    with get_cursor(dbh, buffered=True) as cursor:
        # we can't use mysql string interpolation to ensure db_name isn't something nasty,
        # so we check it against the list of existing databases:
        sql = 'SHOW DATABASES'
        cursor.execute(sql)
        dbs = [t[0] for t in cursor]
        if db_name not in dbs:
            raise ValueError('no such database: {}'.format(db_name))

        sql = 'SHOW TABLES FROM {}'.format(db_name)
        cursor.execute(sql)
        return [t[0] for t in cursor]

def get_field_info(dbh, tablename):
    '''
    Returns:
    - obj_fields gets a list of the columns in the table
    - column_info get a dict keyed on column name; holds col_type, null_ok, key, default, extra, an py_type
    - primary_key gets the name of the primary key of the table (fixme: support for multiple-column primary keys?)
    '''
    # get all the field names from the table:

    with get_cursor(dbh) as cursor:
        cursor.execute("SHOW COLUMNS FROM {}.{}".format(get_database(dbh), tablename))
        obj_fields = []    # contains list of field names
        column_info = {}   # contains dict of field info as derived from "SHOW COLUMNS"
        primary_key = None
        for row in cursor:
            col_name, col_type, null_ok, key, default, extra = row
            obj_fields.append(col_name)
            py_type = mysql_t2t(col_type)
            if py_type is datetime.datetime:
                py_type = str # see hack in parse_args() below
            column_info[col_name] = {
                'col_type': col_type,
                'null_ok': null_ok,
                'key': key,
                'default': default,
                'extra': extra,
                'py_type': py_type,
                }
            if 'PRI' in key:
                primary_key = col_name

        obj_fields.sort()
        return obj_fields, column_info, primary_key

def mysql_t2t(mytype):
    ''' take a mysql type as returned by "show columns from <tablename>" and return a python type '''
    mytype = mytype.lower()
    if 'bit' in mytype or 'bool' in mytype:
        return bool
    elif 'int' in mytype or 'integer' in mytype or 'dec' in mytype:
        return int
    elif 'float' in mytype or 'double' in mytype:
        return float
    elif  'datetime' in mytype:
        return datetime.datetime
    elif 'date' in mytype:
        return datetime.date
    elif 'timestamp' in mytype:
        return str
    elif 'time' in mytype:
        return datetime.time
    elif 'char' in mytype or 'text' in mytype:
        return str
    else:
        raise ValueError("unknown mysql type '{}'".format(mytype))
    

def _get_cursor(dbh, **cursor_args):
    if PYTHON2:
        return dbh.cursor(**cursor_args)
    elif PYTHON3:
        return dbh.cursor()
        
@contextmanager
def get_cursor(dbh, **cursor_args):
    # if type(dbh) is not mysql.connector.connection.MySQLConnection:
    #     raise TypeError(dbh)
    try:
        try:
            cursor = _get_cursor(dbh, **cursor_args)
        except OperationalError as e:
            # reconnect and try again
            dbh.reconnect()
            cursor = dbh.cursor(**cursor_args)
        yield cursor

    except Exception as e:
        raise                   # why? 
    finally:
        cursor.close()      # raises UnboundLocalVar on fail to create cursor; usually a threading error
        dbh.commit()


def do_sql(cursor, sql, values=tuple(), f=sys.stderr):
    ''' just execute sql, but also print sql to stderr (or some other file) if $DEBUG set. '''
    if os.environ.get('DEBUG', False):
        f.write('{}, values={}\n'.format(sql, str(values)))
    cursor.execute(sql, values)

def clear_table(dbh, db_name, table):
    with get_cursor(dbh) as cursor:
        sql = "DELETE FROM {}.{}".format(db_name, table)
        do_sql(cursor, sql)
    

def save_obj(dbh, record, tablename, primary_key=None, debug=False):
    ''' 
    cause an object (record) to be saved.
    '''
    sql, all_values = build_upsert_sql(record, tablename, primary_key)
    with get_cursor(dbh) as cursor:
        cursor.execute(sql, all_values)
        try:
            return cursor.lastrowid
        except _MysqlError as e:
            # when primary key was provided?
            return None


def build_upsert_sql(record, tablename, primary_key=None):
    '''
    return sql that implements an 'UPSERT' operation; it will insert the record if it doesn't exist, update it if does 
    (according to the primary id).

    record: a dict containing the record to be saved.

    returns: a tuple of (sql, values)
    '''
    fields = record.keys()
    all_values = [record.get(key) for key in fields] # don't use record.values() because order probably not guaranteed
    n_percents = '({})'.format(', '.join(['%s'] * len(fields)))

    sql = 'INSERT INTO {} ({}) VALUES {}'.format(tablename, ', '.join(fields), n_percents)
    if primary_key is not None:
        other_fields = copy.copy(fields)
        if primary_key in other_fields:
            other_fields.remove(primary_key)
        updates = ', '.join(['{}=%s'.format(field) for field in other_fields])
        sql +=  ' ON DUPLICATE KEY UPDATE {}'.format(updates)
        for field in other_fields:
            all_values.append(record[field]) # yes, again        

    return sql, all_values

    
def table_exists(dbh, tablename):
    with get_cursor(dbh) as cursor:
        try:
            do_sql(cursor, 'SELECT COUNT(*) FROM {}'.format(tablename))
            list(cursor)        # suck up cursor contents
            return True
        except _MysqlError as e:
            return False

def pw_encrypt(pwd):
    ''' shim for encryption functionality '''
    return md5(pwd).hexdigest()


@contextmanager
def lock_tables(cursor, tablename, db_names):
    tables = ', '.join(['{}.{} WRITE'.format(db_name, tablename) for db_name in db_names])
    sql = 'LOCK TABLE {}'.format(tables)
    cursor.execute(sql)
    yield
    cursor.execute('UNLOCK TABLES')

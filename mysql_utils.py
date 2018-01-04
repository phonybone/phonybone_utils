import sys
import os
import copy
import mysql.connector
from contextlib import contextmanager
import ConfigParser
import sqlalchemy as sa
from mysql.connector.errors import Error as _MysqlError
from everest_core import log

def get_mysql(host, database, user, password):
    ''' Connect to a mysql database. '''
    return mysql.connector.connect(host=host, database=database, user=user, password=password)

def get_mysql_cmdline(opts):
    ''' Connect to a mysql database based on cmd-line options.  
    Also looks in ~/.my.cnf for missing values, args in opts have precedence.
    opts is a Namespace object as returned by argparse.parse_args()
    '''
    conn_args = {}
    for arg in ['host', 'db', 'user', 'password']:
        if hasattr(opts, arg):
            conn_args[arg] = getattr(opts, arg)

    with open(os.path.join('/home', os.environ.get('USER'), '.my.cnf')) as f:
        config = ConfigParser.SafeConfigParser()
        config.readfp(f)
        if config.has_section('mysql'):
            if 'user' not in conn_args or not conn_args['user']:
                try:
                    conn_args['user'] = config.get('mysql', 'user')
                except Exception as e:
                    pass
            if 'password' not in conn_args or not conn_args['password']:
                try:
                    conn_args['password'] = config.get('mysql', 'password')
                except Exception as e:
                    print 'no password: {} {}'.format(type(e), e)
                    pass

    if opts.d:
        print 'mysql connection: {}'.format(conn_args)
    return mysql.connector.connect(**conn_args)
    
        
@contextmanager
def get_cursor(dbh, **cursor_args):
    try:
        cursor = dbh.cursor(**cursor_args)
        yield cursor
    finally:
        try:
            cursor.close()      # raises on fail to create cursor
            dbh.commit()
        except UnboundLocalError:
            pass


def do_sql(cursor, sql, values=tuple(), f=sys.stderr):
    ''' just execute sql, but also print sql to stderr (or some other file) if $DEBUG set. '''
    if os.environ.get('DEBUG', False):
        f.write('{}, values={}\n'.format(sql, str(values)))
    cursor.execute(sql, values)

def clear_table(dbh, db_name, table):
    with get_cursor(dbh) as cursor:
        sql = "DELETE FROM {}.{}".format(db_name, table)
        do_sql(cursor, sql)
    
def get_db_names(config, section='mysql', key_suffix='_database'):
    ''' return a dict mapping of database names.  Key is config key, value is database name '''
    db_names = {opt:config.get(section, opt) for opt in filter(lambda opt: opt.endswith(key_suffix), config.options(section))}
    return db_names


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
            log.exception(e)
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
            list(cursor)
            return True
        except _MysqlError as e:
            print e
            return False

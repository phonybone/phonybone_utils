from pbutils.mysql_utils import get_cursor

def create_db(dbh, database='pbutils_test'):
    with get_cursor(dbh) as cursor:
        sql = 'DROP DATABASE IF EXISTS {}'.format(database)
        cursor.execute(sql)
        sql = 'CREATE DATABASE {}'.format(database)
        cursor.execute(sql)
        

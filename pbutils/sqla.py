'''
SqlAlchemy classes.

All classes used by our SqlAlchemy utilization are defined here.
'''

import logging
log = logging.getLogger(__name__)

import sys
PYTHON2 = sys.version_info[0] == 2
PYTHON3 = sys.version_info[0] == 3
assert PYTHON2 or PYTHON3


from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pbutils.dicts import hashsubset
from pbutils.strings import qw
from pbutils.configs import to_dict, get_config

# To install mysql connector (works on MacOSX, too):
# pip install mysql-connector-python-rf
# see https://stackoverflow.com/questions/24272223/import-mysql-connector-python


from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
Session = None
engine = None

def sqlA_init_from_config_fn(config_fn, section):
    '''
    Extract db connection information from config/section.  The following keys must be present in the config section:
    host, database, user, password
    '''
    config = get_config(config_fn)
    return sqlA_init_from_config(config, section)

def sqlA_init_from_config(config, section):
    conn_args = hashsubset(to_dict(config, section), *qw('host database user password'))
    return sqlA_init(**conn_args)

def sqlA_init(host, database, user, password):
    ''' 
    Initialize all stuff we need for SqlAlchemy: gets engine, creates all classes, creates and returns Session
    Return the Session classed needed to create sessions
    '''
    global engine, Session
    engine = get_SqlA_mysql_engine(host, database, user, password)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session


def get_SqlA_mysql_engine(host, database, user, password):
    if PYTHON2:
        dialect = 'mysql+mysqlconnector'
    elif PYTHON3:
        dialect = 'mysql+pymysql'
    eng_str = '{dialect}://{user}:{password}@{host}/{database}'.format(
        dialect=dialect, user=user, password=password, host=host, database=database)
    return create_engine(eng_str)

@contextmanager
def get_session(**session_args):
    session = Session(**session_args)
    try:
        yield session
        try:
            session.commit()
        except Exception as e:
            log.exception(e)

    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def session_dbh(session):
    return session.connection().connection.connection


if __name__ == '__main__':
    password = ''.join([chr(c) for c in [66, 115, 97, 52, 52, 49]])
    sqlA_init(host='localhost', database='Everest', user='victor', password=password)
    from everest_core.user_classes.user import User
    from everest_core.user_classes.lab import Lab

    with get_session() as session:
        print('\n'.join([str(user) for user in session.query(User).all()]))
    print('yay')

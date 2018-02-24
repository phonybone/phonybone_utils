'''
SqlAlchemy classes.

All classes used by our SqlAlchemy utilization are defined here.
'''

import logging
log = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from everest_core import testing_mode
from everest_core.utils.dicts import hashsubset
from everest_core.utils.strings import qw
from everest_core.utils.configs import to_dict, get_config
from contextlib import contextmanager

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
    host, shared_database, user, password
    '''
    config = get_config(config_fn)
    return sqlA_init_from_config(config, section)

def sqlA_init_from_config(config, section):
    conn_args = hashsubset(to_dict(config, section), *qw('host shared_database user password'))
    conn_args['database'] = conn_args.pop('shared_database')
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
    if testing_mode() and not database.endswith('_dev'):
        database = '{}_dev'.format(database) # really the best place for this code????
    eng_str = 'mysql+mysqlconnector://{user}:{password}@{host}/{database}'.format(
        user=user, password=password, host=host, database=database)
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

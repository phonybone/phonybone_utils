import unittest
import pkg_resources as pr

from pbutils.sqla import sqlA_init_from_config_fn
from pbutils.configs import get_config
from pbutils.mysql_utils import get_mysql
from pbutils.strings import qw
from pbutils.tests import create_db

class SqlaTest(unittest.TestCase):
    def test_init(self):
        mysql_ini = pr.resource_filename('pbutils', 'tests/fixtures/mysql.ini')
        config = get_config(mysql_ini)
        database = config.get('mysql', 'database')
        print('using database "{}"'.format(database))
        args = dict(config.items('mysql'))
        args['database'] = 'mysql'
        dbh = get_mysql(**args)
        create_db(dbh, database)
        print('{} created'.format(database))
        Session = sqlA_init_from_config_fn(mysql_ini, 'mysql')
        print('Session: {}'.format(Session))

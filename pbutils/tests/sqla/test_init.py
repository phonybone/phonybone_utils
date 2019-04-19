import unittest
import pkg_resources as pr
from sqlalchemy.orm.session import sessionmaker

from pbutils.sqla import sqlA_init_from_config_fn
from pbutils.configs import get_config
from pbutils.mysql_utils import get_mysql
from pbutils.tests import create_db


class SqlaTest(unittest.TestCase):
    def test_init(self):
        ''' test initialization using sqlA_init_from_config_fn() '''
        mysql_ini = pr.resource_filename('pbutils', 'tests/fixtures/mysql.ini')
        config = get_config(mysql_ini)
        database = config.get('mysql', 'database')
        args = dict(config.items('mysql'))
        args['database'] = 'mysql'
        dbh = get_mysql(**args)
        create_db(dbh, database)
        Session = sqlA_init_from_config_fn(mysql_ini, 'mysql')
        self.assertEqual(type(Session), sessionmaker)

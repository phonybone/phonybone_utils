import unittest
import pkg_resources as pr

from pbutils.mysql_utils import get_mysql, get_tables, get_database
from pbutils.configs import get_config
from pbutils.strings import qw

class TestGetMysql(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_get_mysql(self):
        config_fn = pr.resource_filename('pbutils', 'tests/fixtures/mysql.ini')
        config = get_config(config_fn)
        self.assertIn('mysql', config.sections())

        db = 'mysql'            # needed for this test
        args = dict(config.items('mysql'))
        args['database'] = db
        dbh = get_mysql(**args)
        self.assertEqual(get_database(dbh), db)
        return dbh
    
    def test_get_tables(self):
        dbh = self.test_get_mysql()
        tables = get_tables(dbh)
        for table in qw('user'):
            self.assertIn(table, tables)


import unittest
import importlib

from pbutils.streams import warn

# Try to import flask settings module:
settings = None
try:
    pkg_root = __name__.split('.')[0]
    settings_modname = '{}.settings'.format(pkg_root)
    settings = importlib.import_module(settings_modname)
except ImportError as e:
    warn('Unable to import {}: {}'.format(settings_modname, str(e)))
    

class BaseTest(unittest.TestCase):
    
    if settings is not None:
        base_url = 'http://{}'.format(settings.FLASK_SERVER_NAME)
    else:
        base_url = 'http://localhost:5000'

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        try:
            self.reset_fixture()
        except AttributeError as e:
            if str(e) == 'reset_fixture':
                print('{} has no method "reset_fixture()", skipping'.format(self.__class__))
            else:
                raise

    def make_url(cls, url):
        return cls.base_url + url

    def _test_status(self, url, method, data, status_code, content_type):
        ''' issue a <method> request on url and verify the expected status_code was found. return resp.json() '''
        real_url = self.make_url(url)
        req = getattr(self.client, method.lower())
        args = {'follow_redirects': True} # not needed for this site, but...
        if data:
            if content_type == 'application/json':
                args['data'] = json.dumps(data)
            elif content_type == 'application/x-www-form-urlencoded':
                args['data'] = data
            args['content_type'] = content_type
        resp = req(real_url, **args) 
        self.assertEqual(resp.status_code, status_code)
        try:
            return json.loads(str(resp.data.decode()))
        except (TypeError, ValueError):
            return resp.data.decode()

    def _test_get_status(self, url, status_code=200):
        return self._test_status(url, 'GET', None, status_code, None)
        
    def _test_post_status(self, url, data, status_code=201, content_type='application/json'):
        return self._test_status(url, 'POST', data, status_code, content_type)
        
    def _test_put_status(self, url, data, status_code=204, content_type='application/json'):
        return self._test_status(url, 'PUT', data, status_code, content_type)
        
    def _test_delete_status(self, url, status_code=204):
        return self._test_status(url, 'DELETE', None, status_code, None)

'''
Define a set of interchangeable classes that yield messages.
They can get the messages from polling a website, a message Q,
or even generate them themself.
'''

#
# Basic iterator functionality: see https://stackoverflow.com/questions/19151/build-a-basic-python-iterator 
#

import requests
import time

class HTTPPoll(object):
    def __init__(self, base_url, login_url, poll_url, username, password, timeout=2.0):
        self.url = base_url + poll_url
        self.cookies = self._login(base_url+login_url, username, password)
        self.timeout = timeout
        
    def __str__(self):
        return 'HTTPPoll({})'.format(self.url)

    def _login(self, url, username, password):
        resp = requests.post(url, data={'username': username, 'password': password})
        resp.raise_for_status()
        return resp.cookies

    def __iter__(self):
        return self

    def next(self):
        if not hasattr(self, 'cookies'):
            raise RuntimeError('{} not logged in?'.format(self))

        while True:
            resp = requests.get(self.url, cookies=self.cookies)
            resp.raise_for_status()
            msg = resp.json()

            if self._valid_msg(msg):
                return msg
            elif self._is_quit_msg(msg):
                raise StopIteration()
            else:
                time.sleep(self.timeout)

    def _valid_msg(self, msg):
        # name should be changed to something more generic; _valid_msg(), maybe...
        return 'success' in msg and msg['success']

    def _is_quit_msg(self, msg):
        return 'quit' in msg and msg['quit']

            
if __name__ == '__main__':
    import sys, os
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(parent_dir)

    from job_service.utils.files import package_fileres
    from job_service.utils.configs import get_config
     from job_service.utils.strings import ppjson
    
    config_fn = package_fileres('job_service', 'config.ini')
    config = get_config(config_fn)
    
    poller = HTTPPoll('http://127.0.0.1:5000',
                      '/login',
                      '/api/runs',
                      config.get('gui_service', 'username'),
                      config.get('gui_service', 'password')
                      )
    fuse = 5
    for msg in poller:
        # print 'got {}'.format(ppjson(msg))
        print 'got {} runs'.format(len(msg['data']))
        fuse -= 1
        if fuse <= 0:
            break


'''
Implement threaded requests
'''

import threading as th
import queue as Q
import requests

from pbutils.request.utils import all_contexts, populate_profile, create_request_params

class ThreadedReq:
    '''
    Threaded requests.
    '''
    def __init__(self, n_threads, config, environ, error_handler=None):
        ''' constructor '''
        self.n_threads = n_threads
        self.config = config
        self.environ = environ
        self.inq = Q.Queue()
        self.outq = Q.Queue()
        self.done = th.Event()
        self.error_handler = error_handler

    def run(self, profiles):
        '''
        Process all profiles: use do_responses to obtain results.
        '''
        for profile in profiles:
            for context in all_contexts(profile, self.environ):
                pprofile = populate_profile(profile, context)
                req_params = create_request_params(pprofile)
                self.inq.put((profile, req_params))

        threads = []
        for _ in range(self.n_threads):
            thread = th.Thread(target=self.do_requests)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        self.done.set()

    def do_requests(self):
        '''
        Read from inq, make the request, and put profile & response
        onto outq.
        '''
        while True:
            try:
                profile, req_params = self.inq.get(block=False)
            except Q.Empty:
                break
            try:
                # resp = None
                resp = requests.request(**req_params)
                resp.raise_for_status()
            except Exception as e:
                if self.error_handler:
                    self.error_handler(profile, resp, e)
                else:
                    raise
            else:
                self.outq.put((profile, resp))

    def do_responses(self):
        '''
        Yield all responses as they occur.
        '''
        while True:
            try:
                profile, resp = self.outq.get(timeout=3)  # to=3 a hack?
                yield profile, resp
                if self.outq.empty() and self.done.is_set():
                    break
            except Q.Empty:
                return

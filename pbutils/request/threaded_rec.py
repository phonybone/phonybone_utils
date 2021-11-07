'''
Implement threaded requests
'''

import threading as th
import queue as Q
import requests

from pbutils.request.utils import all_contexts, populate_profile, create_request_params

class ThreadedReq:
    def __init__(self, n_threads, config, environ):
        self.n_threads = n_threads
        self.config = config
        self.environ = environ
        self.inq = Q.Queue()
        self.outq = Q.Queue()

    def run(self, profiles):
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

    def do_requests(self):
        while True:
            try:
                profile, req_params = self.inq.get(block=False)
            except Q.Empty:
                break
            resp = requests.request(**req_params)
            self.outq.put((profile, resp))

    def do_responses(self):
        while True:
            try:
                profile, resp = self.outq.get(timeout=3)
                yield profile, resp
            except Q.Empty:
                return

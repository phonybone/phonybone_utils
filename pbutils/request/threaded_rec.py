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
                print(F"put {profile['url']} onto inq")

        threads = []
        for _ in range(self.n_threads):
            thread = th.Thread(target=self.do_requests)
            thread.start()
            threads.append(thread)

        for thread in threads:
            print(F"waiting on {thread.name}.join")
            thread.join()
            print(F"{thread.name} joined")

    def do_requests(self):
        print(F"do_requests starting")
        # while not self.inq.empty:
        while True:
            print(F"fetching from inq")
            try:
                profile, req_params = self.inq.get(block=False)
            except Q.Empty:
                break
            print(F"fetching {req_params['url']}")
            resp = requests.request(**req_params)
            print(F"putting (profile, resp) onto self.outq")
            self.outq.put((profile, resp))
        print(F"do_requets done, bye")

    def do_responses(self):
        while True:
            try:
                profile, resp = self.outq.get(timeout=3)
                print(F"do_responses yielding")
                yield profile, resp
            except Q.Empty:
                print(F"do_responses done")
                return

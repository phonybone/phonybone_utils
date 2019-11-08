import json
import re
from urllib.parse import parse_qs
import atexit
import threading
from collections import namedtuple
from uuid import uuid4
import logging

from flask import Flask, render_template, request
import waitress
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import MethodNotAllowed, NotFound


CapturedRequest = namedtuple('CapturedRequest', ['id', 'path', 'args', 'method', 'headers', 'body'])


class Sham:
    ''' Encapsulate sham server as an object. '''
    def __init__(self, response_fn, name=__name__, port=6000, n_threads=4, daemon=False, logger=None, log_lvl=logging.DEBUG):
        self.requests = []
        self.request_lock = threading.RLock()
        self.app = Flask(name)
        self.port = port
        self.n_threads = n_threads
        self.app.debug = True
        self.daemon = daemon
        self.logger = logger
        self.log_lvl = log_lvl

        with open(response_fn) as f:
            self.responses = json.load(f)

        for resp_list in self.responses.values():
            for resp in resp_list:
                resp['args'] = ImmutableMultiDict(resp.get('args', {}))
        self.log(F"sham open for business on port {self.port}")

    def log(self, message, level=None):
        if self.logger:
            if level is None:
                level = self.log_lvl
            self.logger.log(level, message)

    def _index(self):
        return render_template('index.html', requests=self.requests)

    def _catch_all(self, path):
        if path == 'favicon.ico':
            return 'Not Found', 404

        if request.is_json:
            data = request.json
        else:
            data = request.data

        cr = CapturedRequest(str(uuid4()), path, dict(request.args), request.method, request.headers, data)
        self.log(F"sham: {request.method} {path} {data}")

        with self.request_lock:
            self.requests.append(cr)
            if len(self.requests) > 10:
                self.requests.pop(0)

        # Here we search self.responses to see if we have a response to return.
        potential_responses = None

        for pattern, responses in self.responses.items():
            regex = re.compile(F"^{pattern}$")
            match = regex.match(cr.path)
            if match:
                if potential_responses:
                    self.log('Multiple path patterns match, please reconfigure responses.')
                    raise IndexError('Multiple path patterns match, please reconfigure responses.')

                potential_responses = responses
                # Any named groups in path will be extracted here
                path_params = match.groupdict()

        if potential_responses is None:
            self.log('NotFound')
            raise NotFound

        for resp in potential_responses:
            if self.args_match(resp, cr) and self.methods_match(resp, cr):
                data = resp['response']

                if isinstance(data, dict):
                    # extra brackets are to prevent format from interpreting keys as references
                    data = '{' + json.dumps(data) + '}'

                if path_params:
                    data = data.format(**path_params)

                if isinstance(data, str):
                    data = re.sub('^{{', '{', data)
                    data = re.sub('}}$', '}', data)

                return data, resp.get('status_code', 200)

        # TODO: MethodNotAllowed is raised both if methods didn't match and if no args didn't match, but ideally the second
        # should raise a different HTTP error.
        self.log('MethodNotAllowed (but could be NoMatchingArgs')
        raise MethodNotAllowed

    @staticmethod
    def args_match(resp: dict, cr: CapturedRequest) -> bool:
        # This is what it was, but there was a bug when `key not in resp['args']`:
        # return all([resp['args'][key] == cr.args[key][0] or resp['args'][key] == '*' for key in cr.args.keys()])

        for key in cr.args.keys():
            if key not in resp['args']:
                return False
            if resp['args'][key] == cr.args[key][0]:
                continue
            if resp['args'][key] == '*':
                continue
            return False
        return True

    @staticmethod
    def methods_match(resp: dict, cr: CapturedRequest) -> bool:
        return not resp.get('methods') or cr.method.lower() in resp['methods'] or resp['methods'] == '*'

    def serve(self):
        self.app.route('/')(self._index)  # can we move these to __init__?
        self.app.route('/<path:path>', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])(self._catch_all)

        if self.daemon:
            def __server():
                waitress.serve(self.app, host='0.0.0.0', port=self.port, threads=self.n_threads)
            t = threading.Thread(target=__server, name='sham_server', daemon=True)
            t.start()
            return t
        else:
            waitress.serve(self.app, host='0.0.0.0', port=self.port, threads=self.n_threads)


class ShamRecorder:
    '''
    A class that can record calls made to a website in a format that can be used later to run sham.
    '''
    def __init__(self, fn):
        self.fn = fn
        self.reqres = {}
        self.url_regex = re.compile(r'https?://([^/]+)/([^?]*)\??(.*)', flags=re.I)
        atexit.register(self.write)

    def record(self, req, res):
        mg = self.url_regex.match(req)
        if mg is None:
            raise ValueError(F"invalid url: {req}")
        domain, path, args = mg.groups()
        args = parse_qs(args)
        self.reqres.setdefault(path, []).append({'args': args, 'response': res})

    def write(self):
        with open(self.fn, 'w') as f:
            json.dump(self.reqres, f, indent=2)

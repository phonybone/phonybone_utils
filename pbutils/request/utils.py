'''
Common functions for [a]sync requests and arequest
'''
import sys
import itertools as it
import importlib
from copy import deepcopy
from pathlib import Path
import json
from urllib.parse import urlencode

from pbutils.dicts import is_scalar, traverse_json, set_path_value, json4
from pbutils.request.logs import log


def expand_profiles(profiles, environ=None):
    ''' generator to yield all request profiles '''
    raise NotImplementedError
    for profile in profiles:
        if not isinstance(profile, dict):
            raise TypeError(F"profile is not a dict ({type(profile)})")
        for context in get_contexts(profile):
            context.update(environ)
            yield context

def all_contexts(profile, environ=None):
    if environ is None:
        environ = {}            # no mutable default args
    for context in get_contexts(profile):
        context.update(environ)
        yield context


def get_contexts(profile):
    '''
    Identify all interpolated variables in the profile, then generate
    and yield individual context dict with interpolated values.
    '''
    # add var "n_repeat" if present:
    n_repeat = profile.pop('n_repeat', None)
    if n_repeat:
        profile.setdefault('vars', {})['n_repeat'] = {"range": {"stop": n_repeat}}

    # collect one value iterator for each variable:
    var_iters = {varname: make_var_iterator(varname, varinfo)
                 for varname, varinfo in profile.pop("vars", {}).items()}

    # yield var context for each set of values:
    varnames = var_iters.keys()
    for varvalues in it.product(*var_iters.values()):
        yield dict(zip(varnames, varvalues))


def make_var_iterator(varname, varinfo):
    ''' create an iterator for the variable "varname" with the info in varinfo '''
    if is_scalar(varinfo):
        return [varinfo]

    if 'range' in varinfo:
        rangeinfo = varinfo['range']
        start = rangeinfo.get('start', 0)
        stop = rangeinfo['stop']
        step = rangeinfo.get('step', 1)
        return range(start, stop, step)

    if 'list' in varinfo:
        return iter(varinfo['list'])  # could be any iterable, really

    raise RuntimeError(F"Don't know how to evaluate path_var {varname}")


def populate_profile(profile, context):
    '''
    Traverse profile; extrapolate any leaf of type str using context.
    Return a new profile based on old.
    '''
    pprofile = deepcopy(profile)
    for path, value in traverse_json(profile, only_leaves=True):
        if isinstance(value, str) and '{' in value:
            value = value.format(**context)
            set_path_value(pprofile, path, value)
    return pprofile


def create_request_params(profile):
    '''
    Build and return a parameter dict based on the profile,
    which can then be used to call request().
    '''
    # need to figure out good way of being able to expand (almost)
    # any entry in the profile (method, auth, timeout....)

    url = profile['url']
    method = profile['method'].upper()
    headers = profile.get('headers', {})
    params = profile.get('params')  # querystring params
    timeout = float(profile.get('timeout', '1000.0'))
    log.debug(F"url: {method} {url}")
    if 'body' in profile:
        mimetype = headers.get('Content-type') or headers.get('content-type') or headers.get('Content-type')
        body = get_body(profile, mimetype)
        if mimetype is None:
            if isinstance(body, str):
                mimetype = headers['Content-type'] = 'text/plain'
            else:
                mimetype = headers['Content-type'] = 'application/json'
        if mimetype == 'application/json':
            body = json.dumps(body)
            log.debug("converting body to json")
    else:
        body = None

    # add auth header to headers if needed:
    if "auth" in profile:
        headers.update(make_auth_header(profile["auth"]))

    # assemble call to request:
    req_params = {
        'url': url,
        'method': method,
        'timeout': timeout
    }

    if params:
        req_params['params'] = params
    if headers:
        req_params['headers'] = headers
    if body:
        req_params['data'] = body

    if 'debug' in profile:
        log.debug(F"request:\n{json4(req_params)}")
    log.debug(as_curl(req_params))
    return req_params


def make_auth_header(auth_info):
    ''' Return a one-element dict: "Authorization": <token> '''
    if "module" in auth_info:
        auth_mod_name = auth_info.get("module", "onauth")
        if 'sys_paths' in auth_info:
            # this allows for relative paths (eg ".") to be included
            sys.path.extend(str(Path(path).resolve()) for path in auth_info['sys_paths'])
        auth_module = importlib.import_module(auth_mod_name)
        ahf_name = auth_info.get("auth_header_function", "make_auth_header")
        make_auth_header = getattr(auth_module, ahf_name)
        auth_header = make_auth_header(auth_info)

        if auth_info.get('log_token', False):
            log.info(json4(auth_header))
        return auth_header

    elif "token_file" in auth_info:
        # token_file should contain a json dict w/keys 'token_type' and 'access_token'
        with open(auth_info['token_file']) as tkn:
            token_info = json.load(tkn)
            return {"Authorization": F"{token_info['token_type']} {token_info['access_token']}"}

    elif "header_file" in auth_info:
        # header_file should contain a json dict {"Authorization": "<token>"}
        with open(auth_info['header_file']) as hf:
            return json.load(hf)

    elif "header_json" in auth_info:  # literal dict
        return auth_info["header_json"]

    else:
        raise RuntimeError("don't know how to make auth header")


def get_body(profile, mimetype):
    '''
    Get the body, either directly from the profile or read from disk
    if profile['body'] is a str and starts with '@'.

    Also, attempt to convert body to data if mimetype=='application/json'.
    '''
    body = profile['body']
    if isinstance(body, str):
        if body.startswith('@'):
            with open(body[1:]) as fyle:
                body = fyle.read()

        if mimetype.lower() == 'application/json':
            try:
                body = json.loads(body)
            except Exception as e:
                log.debug(F"Could not convert body to json, leaving as {type(body)} ({type(e)}: {e})")

    return body


def as_curl(req_params):
    cmd = ['curl', '--location', '--request', req_params['method']]
    url = req_params['url']
    if 'params' in req_params:
        url += '?' + urlencode(req_params['params'])
    cmd.append(url)

    for key, value in req_params.get('headers', {}).items():
        cmd.append(F"--header '{key}: {value}'")

    # --data goes here
    return " \\\n".join(cmd)    # one part of cmd[] per line, with trailing '\'s

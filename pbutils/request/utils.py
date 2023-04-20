'''
Common functions for [a]sync requests and arequest
'''
import sys
import os
import itertools as it
import importlib
import requests
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
    '''
    Create an iterator for the variable "varname" with the info in varinfo.

    If varinfo is a scalar, create a one-element list with the value.
    If varinfo is a list (literal), return that.
    Otherwise, varinfo should be a dict of a particular "flavor":
    - varinfo['range'] -> return range(start, stop, step) (with defaults)
    - 
    '''
    if is_scalar(varinfo):
        return [varinfo]

    if isinstance(varinfo, list):  # list literal
        return varinfo

    if 'range' in varinfo:      # generate using range()
        rangeinfo = varinfo['range']
        if isinstance(rangeinfo, dict):  # named range() params
            start = rangeinfo.get('start', 0)
            stop = rangeinfo['stop']
            step = rangeinfo.get('step', 1)
            return range(start, stop, step)
        elif isinstance(rangeinfo, list):  # implied range() params
            return range(*rangeinfo)
        else:
            raise RuntimeError("Don't know how to make an iterator from '{rangeinfo}'")

    if 'list' in varinfo:            # named list literal; basically same as above
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
            try:
                value = value.format(**context)
                set_path_value(pprofile, path, value)
            except Exception as e:
                print(F"populate: caught {type(e)}: {e}")
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
    log.debug(F"url: {method} {url}")
    headers = profile.get('headers', {})
    params = profile.get('params')  # querystring params
    timeout = float(profile.get('timeout', '1000.0'))

    data = get_data(profile)

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
    if data:
        req_params['data'] = data
    if 'debug' in profile:
        log.debug(F"request:\n{json4(req_params)}")
    # log.debug(as_curl(req_params))
    return req_params


def make_auth_header(auth_info):
    '''
    Return a one-element dict: "Authorization": <token>

    auth_info contains:
    - module: execute and return code specified by value (dict)
    - token_file: value is name of file containing json dict with 'access_token' and 'token_type'
    - header_file: value is name of file containing json dict with 'Authorization'
    - header_json: value is dict with header info (should be "header_dict")
    - request: value contains info to make an HTTP request that returns an Authorization header entry
    '''
    if "module" in auth_info:
        auth_mod_name = auth_info["module"]
        if 'sys_paths' in auth_info:
            # this allows for relative paths (eg ".") to be included
            sys.path.extend(str(Path(path).resolve()) for path in auth_info['sys_paths'])

        this_dir = Path(os.path.dirname(__file__)).resolve()
        sys.path.append(str(this_dir))

        auth_module = importlib.import_module(auth_mod_name)
        ahf_name = auth_info.get("auth_header_function", "make_auth_header")
        make_auth_header_func = getattr(auth_module, ahf_name)
        auth_header = make_auth_header_func(auth_info)

        if auth_info.get('log_token', False):
            log.info(json4(auth_header))
        return auth_header

    elif "token_file" in auth_info:
        # token_file should contain a json dict w/keys 'token_type' and 'access_token'
        with open(auth_info['token_file']) as tkn:
            try:
                token_info = json.load(tkn)
            except Exception as e:
                log.error(f"unable to json-decode {auth_info['token_file']}: {e}")
                raise

            return {"Authorization": F"{token_info['token_type']} {token_info['access_token']}"}

    elif "header_file" in auth_info:
        # header_file should contain a json dict {"Authorization": "<token>"}
        with open(auth_info['header_file']) as hf:
            return json.load(hf)

    elif "header_json" in auth_info:  # literal dict
        return auth_info["header_json"]

    elif "request" in auth_info:
        return make_auth_request(auth_info)

    else:
        raise RuntimeError("don't know how to make auth header")


def get_data(profile):
    '''
    Get the data for a POST/PUT/PATCH request.
    Supported types:
    profile['body']: straight text
    profile['data']: dict
    # profile['json']: string in JSON format

    Not yet supported: files
    Does not do anything with profile['headers']
    '''
    data = None
    if 'data' in profile:
        data = profile['data']
        if isinstance(data, str) and data.startswith('@'):
            with open(data[1:]) as fyle:
                data = fyle.read()
        else:
            assert isinstance(data, dict) or isinstance(data, list)

    elif 'body' in profile:
        data = profile.pop('body')  # backwards compatibility

    if "data-post-process" in profile:
        data = post_process(profile["data-post-process"], data)
        data = data
    return data


def post_process(fq_func_name, data):
    ''' post-process request data '''
    # who uses this?
    sys.path.append(os.getcwd())

    parts = fq_func_name.split('.')
    if len(parts) < 2:
        log.debug(F"{fq_func_name}: not enough parts")
        return data
    mod_name = '.'.join(parts[:-1])
    func_name = parts[-1]
    try:
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
    except (ImportError, AttributeError) as e:
        log.debug(F"Cannot import {fq_func_name}: caught {type(e)}: {e}")
        return data

    # apply func:
    try:
        data = func(data)
    except Exception as e:
        log.debug(F"Error running {fq_func_name}(data): caught {type(e)}: {e}")
    return data


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


def make_auth_request(auth_info):
    '''
    Get a token by requesting one from an outside source.
    All request params must be in auth_info['request']
    Checks cache if asked;
    '''
    req_params = auth_info['request']

    # check for previously cached result
    if 'cache_path' in auth_info or auth_info.get('override_cache', False):
        try:
            with open(auth_info['cache_path']) as cache:
                log.debug(F"returning cached token in {auth_info['cache_path']}")
                token = json.load(cache)
                return {"Authorization": "Bearer " + token['access_token']}
        except FileNotFoundError as e:
            log.debug(F"{e}, attempting to authorize")

    # get request info from file?
    if isinstance(req_params, str) and req_params.startswith('@'):
        log.debug(F"getting auth request info from {req_params[1:]}")
        with open(req_params[1:]) as fyle:
            req_params = json.load(fyle)

    req_params.pop('method', None)
    resp = requests.post(**req_params)
    resp.raise_for_status()
    token = resp.json()
    if 'access_token' not in token:
        log.warning(F"error in auth request: {json4(token)}")
        raise RuntimeError("authorization failed")

    if 'cache_path' in auth_info:
        with open(auth_info['cache_path'], 'w') as cache:
            print(json4(token), file=cache)
            log.debug(F"cached token info to {auth_info['cache_path']}")

    return {"Authorization": "Bearer " + token['access_token']}


def default_error_handler(profile, response, exc):
    url = response.request.url if response else profile['url']
    status_code = response.status_code if response else '<unknown>'
    print(F"{url}: {status_code}: caught {type(exc)}: {exc}", file=sys.stderr)

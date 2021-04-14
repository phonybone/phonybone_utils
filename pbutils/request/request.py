#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
General purpose script to make an HTTP request and display the results.
Requests are configured by supplying a profile.json file.

Author: Victor Cassen
vmc.swdev@gmail.com
'''
# todo:
# - asyncio
# add profile['n_count']
# add path-param ranges (eg to iterate over /user/{id}
# add onauth.py & jwt.py


import os
import json
# import requests
import logging
import importlib
import itertools as it

from pbutils.argparsers import parser_stub, wrap_main

# from resp_report import resp_report
from logs import log


def main(config):
    # read url, params, timeout, header(s), request body, all as needed
    profiles = get_profiles(config.arg[0])
    if 'DEBUG' in os.environ:  # could have been set elsewhere besides profile
        log.setLevel(logging.DEBUG)

    reqs = []
    for profile in profiles:
        log.debug(F"profile: {json.dumps(profile, indent=4)}")
        # expand all template variables or other iteration data
        for context in expand(profile):
            req = create_req_params(profile, context)
            print(json.dumps(req, indent=4))
            reqs.append(req)

def expand(profile):
    '''
    Identify all interpolated variables in the profile, then generate
    and yield individual profile dict with interpolated values.
    '''
    # Identify interpolated vars:
    var_iters = {}
    for varname, varinfo in profile.get("vars", {}).items():
        var_iters[varname] = make_var_iterator(varname, varinfo)

    varnames = var_iters.keys()
    for varvalues in it.product(*var_iters.values()):
        yield dict(zip(varnames, varvalues))


def make_var_iterator(varname, varinfo):
    if 'range' in varinfo:
        rangeinfo = varinfo['range']
        start = rangeinfo.get('start', 0)
        stop = rangeinfo['stop']
        step = rangeinfo.get('step', 1)
        return range(start, stop, step)
    elif 'list' in varinfo:
        return varinfo['list']
    else:
        raise RuntimeError(F"Don't know how to evaluate path_var {varname}")


def create_req_params(profile, context):
    ''' build and return a parameter dict based on the profile. '''
    # need to figure out good way of being able to expand (almost)
    # any entry in the profile (method, auth, timeout....)
    headers = {}
    req_data = None
    payload = None

    url = profile['url'].format(**context)
    params = {k:v.format(**context) for k,v in profile['params'].items()}
    timeout = float(profile.get('timeout', '1000.0'))
    method = profile['method'].upper()
    if method in {'POST', 'PUT', 'PATCH'}:
        content_type = profile.get('content-type', 'application/json')
        content_header = {'Content-type': content_type}
        headers.update(**content_header)

        # request_data is meant for json data:
        if 'request_data' in profile:
            req_data = get_req_data(profile)
        elif 'payload' in profile:
            req_data = get_payload(profile)

    # add auth header to headers if needed:
    if "auth" in profile:
        auth_info = profile["auth"]
        headers.update(make_auth_header(auth_info))

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
    if req_data:
        req_params['data'] = req_data
    if payload:
        req_params['payload'] = payload

    if 'debug' in profile:
        print(F"request:\n{json.dumps(req_params, indent=4)}")
    return req_params


def make_auth_header(auth_info):
    if "module" in auth_info:
        auth_mod_name = auth_info.get("module", "onauth")
        auth_module = importlib.import_module(auth_mod_name)
        ahf_name = auth_info.get("auth_header_function", "make_auth_header")
        make_auth_header = getattr(auth_module, ahf_name)
        return make_auth_header(auth_info)

    elif "token_file" in auth_info:
        with open(auth_info['token_file']) as tkn:
            token_info = json.load(tkn)
            return {"Authorization": F"{token_info['token_type']} {token_info['access_token']}"}

    elif "header_file" in auth_info:  # auth header in .json file
        with open(auth_info['header_file']) as hf:
            return json.load(hf)

    elif "header_json" in auth_info:  # literal dict
        return auth_info["header_json"]

    else:
        raise RuntimeError("don't know how to make auth header")

def get_req_data(profile):
    req_data = profile['request_data']
    if isinstance(req_data, str):
        log.info(F"loading update data from {req_data}")
        with open(req_data) as upd:
            req_data = json.load(upd)
            log.info("  data loaded")
    assert type(req_data) in (list, dict)
    req_data = json.dumps(req_data)  # only required for JSONB fields? or always?
    return req_data

def get_payload(profile):
    # while payload is meant for other types, eg application/octet-stream
    if profile['payload'].startswith('@file:'):
        filename = profile['payload'].replace('@file:', '').strip()
        with open(filename) as f:
            req_data = f.read()
    else:
        req_data = profile['payload']
    return req_data


def get_profiles(profile_fn):
    with open(profile_fn) as prf:
        profiles = json.load(prf)
    if isinstance(profiles, dict):
        profiles = [profiles]
    if not isinstance(profiles, list):
        raise ValueError(F"profile_fn: must contain list (got {type(profiles)})")
    return profiles


def make_parser():
    parser = parser_stub(__doc__)
    # parser.add_argument('--', help='')
    parser.add_argument('arg', nargs='*')

    return parser

if __name__ == '__main__':
    parser = make_parser()
    wrap_main(main, parser)

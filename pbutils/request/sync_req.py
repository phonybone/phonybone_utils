from typing import List
import requests
from pbutils.request.utils import expand_profiles


def run(profiles: List[dict], environ=None):
    if isinstance(profiles, dict):
        profiles = [profiles]
    with requests.Session() as session:
        for req_params in expand_profiles(profiles, environ):
            yield do_request(req_params, session)


def do_request(req_params, session):
    ''' Issue request synchronously; return json or content '''
    return session.request(**req_params)

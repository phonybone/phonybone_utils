from typing import List
import json
import requests
from pbutils.request.utils import create_request_params, all_contexts, populate_profile
from pbutils.request.logs import log


def run_sync(profiles: List[dict]):
    for profile, response in run_profiles(profiles):
        yield profile, response


def run_profiles(profiles: List[dict], environ=None):
    '''
    Run each profile once for each generated context.
    As a side effect, persist the response as requested in profile.

    Yield each response.
    '''
    if isinstance(profiles, dict):  # listify
        profiles = [profiles]

    with requests.Session() as session:
        for profile in profiles:
            for context in all_contexts(profile, environ):
                pprofile = populate_profile(profile, context)
                req_params = create_request_params(pprofile)
                response = session.request(**req_params)
                yield profile, response


def handle_response(profile, response, config):
    try:
        content = response.json()
        content = json.dumps(content, indent=4)
    except Exception:
        content = response.text

    summary = F"{response.request.url}: {response.status_code}"

    if 'output_path' in profile:
        with open(profile['output_path'], 'w') as output_stream:
            output_stream.write(content)
            log.debug(F"{profile['output_path']} written")
            print(F"{profile['output_path']} written")
    elif config.verbose:
        print(summary)
        print(content)
    elif not config.silent:
        print(summary)


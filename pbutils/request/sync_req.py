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

                # output_path = pprofile.pop('output_path', None)
                # if output_path:
                #     response.output_path = output_path

                yield profile, response


def handle_response(profile, response, config):
    try:
        content = response.json()
        content = json.dumps(content, indent=4)
    except Exception:
        content = response.text

    if not response.ok:
        log.debug(F"{response.request.url}: {response.status_code}")
        output = content
    else:
        output = F"{response.request.url}: {response.status_code}\n{content}"

    if 'output_path' in profile:
        with open(profile['output_path'], 'w') as output_stream:
            print(output, file=output_stream)
            log.debug(F"{response.output_path} written")
    elif config.verbose:
        print(output)

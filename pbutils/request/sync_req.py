from typing import List
import json
import requests
from pbutils.request.utils import create_request_params, all_contexts, populate_profile


def run_sync(profiles: List[dict]):
    for response in run_profiles(profiles):
        try:
            content = response.json()
            content = json.dumps(content, indent=4)
        except Exception:
            content = response.text

        if 200 <= response.status_code <= 299:
            output = content
        else:
            output = F"{response.request.url}: {response.status_code}\n{content}"

        if hasattr(response, 'output_path'):
            with open(response.output_path, 'w') as output_stream:
                print(output, file=output_stream)
                print(F"{response.output_path} written")
        else:
            print(output)


def run_profiles(profiles: List[dict], environ=None):
    '''
    Run each profile once for each generated context.
    As a side effect, persist the response as requested in profile.

    Yield each response.
    '''
    if isinstance(profiles, dict):
        profiles = [profiles]
    with requests.Session() as session:
        for profile in profiles:
            for context in all_contexts(profile, environ):
                profile = populate_profile(profile, context)
                req_params = create_request_params(profile)
                response = session.request(**req_params)

                output_path = profile.pop('output_path', None)
                if output_path:
                    response.output_path = output_path

                yield response

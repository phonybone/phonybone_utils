import requests
import json
from functools import partial

from pbutils.request.utils import expand_profiles
from pbutils.request.logs import log

json4 = partial(json.dumps, indent=4)


def run(profiles):
    with requests.Session() as session:
        for req_params in expand_profiles(profiles):
            do_request(req_params, session)


def do_request(req_params, session):
    ''' Issue request synchronously; capture output if requested '''
    output_path = req_params.pop('output_path', None)

    response = session.request(**req_params)
    try:
        content = json4(response.json())
    except Exception:
        content = response.text

    if output_path:
        with open(output_path, "w") as output:
            output.write(content)
            log.info(F"{output_path} written")
        req_params['output_path'] = output_path  # restore this because the next request might need it
    else:
        print(content)

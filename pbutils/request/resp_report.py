import os
import json
from logs import log

def resp_report(resp):
    if 'DEBUG' in os.environ:
        log.info(F"{resp.request.method} {resp.request.url}: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(F"{json.dumps(data, indent=4)}")
    else:
        try:
            err_msg = json.dumps(resp.json(), indent=4)
        except:
            err_msg = resp.text
        print(F"{resp.request.method}: {resp.url}: {err_msg} {resp.status_code}")

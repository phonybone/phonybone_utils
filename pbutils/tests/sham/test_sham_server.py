import requests
import threading
import json
from pbutils.sham import Sham
import pytest


@pytest.mark.skip('causes tests to hang, do a better test')
def test_sham_server():
    response_fn = 'tests/sham/example_responses.json'

    def server(response_fn):
        sham = Sham(response_fn)
        print("calling sham.serve()")
        sham.serve()
    t = threading.Thread(target=server, args=(response_fn,), name='server', daemon=True)
    t.start()

    with open(response_fn) as f:
        reqs = json.load(f)

    for url, req_data in reqs.items():
        url = F"http://localhost:6000/{url}"
        for r in req_data:
            print()
            for method in r.get('methods', ['get']):
                rmeth = getattr(requests, method)
                try:
                    resp = rmeth(url, params=r['args'])
                    resp.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    print(F"{resp.url}:  {method.upper()} not allowed")
                    print(F"  {e}")
                    continue

                try:
                    print(F"got back JSON: {resp.json()}")
                except json.decoder.JSONDecodeError:
                    print(F"got back TEXT: {resp.text}")

    print('yay')

'''
Launch a sham server with daemon=True.  Note that this test hangs until it gets
a KeyboardInterrupt, so you have to kill it manually.  Hence the name of the test
has had a '_' prepened to prevent it running.
'''
from pbutils.sham import Sham


def test_sham_server():
    response_fn = 'tests/sham/example_responses.json'
    sham = Sham(response_fn, daemon=True)
    t = sham.serve()
    print('waiting')
    try:
        t.join()
    except KeyboardInterrupt:
        print('yay')

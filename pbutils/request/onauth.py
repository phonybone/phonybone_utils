import datetime as dt
import json
import subprocess as sp
from pbutils.jwt_util import create_jwt_token
from pbutils.request.utils import make_auth_request


def make_auth_header(profile):
    auth_info = profile['auth']
    if auth_info is None:
        return {}
    if 'email' in auth_info and 'account' in auth_info:
        return make_onroute_auth_header(auth_info)
    elif 'token_file' in auth_info and 'token_type' in auth_info:
        return make_rtb_auth_header(auth_info)
    elif 'request' in auth_info:
        return make_auth_request(auth_info)
    elif 'gcloud' in auth_info:
        return make_gcloud_auth_header(auth_info)
    else:
        raise RuntimeError("can't make auth header: missing info")


def make_onroute_auth_header(auth_info):
    '''
    Make an auth token for Onroute

    auth_info is a dict.  Needs to have 'email' and 'account'
    '''
    content = dict(
        email=auth_info['email'],
        account=auth_info['account'],
        is_zonar=False,
        sub="access"            # according to onroute-api/app/core/config.py
    )
    expires = dt.timedelta(minutes=60*24*7)
    token = create_jwt_token(
        jwt_content=content,
        jwt_subject='whatevs',
        secret_key='Zonar!',
        expires_delta=expires)
    if isinstance(token, bytes):
        token = token.decode()
    return {'Authorization': f'ONROUTE {token}'}


def make_rtb_auth_header(auth_info):
    with open(auth_info['token_file']) as tkn:
        data = json.load(tkn)
        access_token = data['access_token']
        token_type = auth_info['token_type']
    return {'Authorization': F"{token_type} {access_token}"}


def make_gcloud_auth_header(auth_info):
    proc = sp.Popen(
        ['gcloud', 'auth', 'print-identity-token'],
        stdout=sp.PIPE
    )
    timeout = int(auth_info.get('timeout', 5))
    token, errs = proc.communicate(timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(F"unable to get id-token: {errs.decode()}")
    return {'Authorization': F"Bearer {token.decode()}"}


if __name__ == '__main__':
    import sys
    from functools import partial
    json2 = partial(json.dumps, indent=2)
    warn = partial(print, file=sys.stderr)

    def die(msg, exit_code=1):
        warn(msg)
        sys.exit(exit_code)

    def test_onroute_auth(account, email):
        resp = make_onroute_auth_header({'email': email, 'account': account})
        print(F"resp is {json2(resp)}")

    ########################################################################
    cmds = [key for key, value in locals().items() if callable(value)]
    usage = F"usage: python onauth.py [{'|'.join(cmds)}]"
    if len(sys.argv) <= 1:
        die(usage)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    method = locals().get(cmd)
    if method is None:
        die(usage)
    method(*args)

    

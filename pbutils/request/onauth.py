import datetime as dt
import json
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

if __name__ == '__main__':
    auth_info = {
        'email': 'dan@testenv.com',
        'account': 'dbr47_rep1023'
    }
    header = make_onroute_auth_header(auth_info)
    print(json.dumps(header, indent=2))

import datetime as dt
import json
from pbutils.jwt_util import create_jwt_token


def make_auth_header(profile):
    auth_info = profile['auth']
    if auth_info is None:
        return {}
    if 'email' in auth_info and 'account' in auth_info:
        return make_onroute_auth_header(auth_info)
    elif 'token_file' in auth_info and 'token_type' in auth_info:
        return make_rtb_auth_header(auth_info)
    else:
        raise RuntimeError("can't make auth header: missing info")


def make_onroute_auth_header(auth_info):
    content = dict(
        email=auth_info['email'],
        account=auth_info['account'],
        is_zonar=False,
        sub="access"            # according to onroute-api/app/core/config.py
    )
    expires = dt.timedelta(minutes=60*24*7)
    token = create_jwt_token(jwt_content=content, secret_key='Zonar!', expires_delta=expires)
    return {'Authorization': f'ONROUTE {token}'}


def make_rtb_auth_header(auth_info):
    with open(auth_info['token_file']) as tkn:
        data = json.load(tkn)
        access_token = data['access_token']
        token_type = auth_info['token_type']
    return {'Authorization': F"{token_type} {access_token}"}


if __name__ == '__main__':
    # Generate ONROUTE token with email & account, store json to file
    import sys

    email = sys.argv[1]
    account_code = sys.argv[2]
    header = make_onroute_auth_header({'email': email, 'account': account_code})

    fn = F"{account_code}.{email}.auth_header.json"
    with open(fn, "w") as f:
        print(json.dumps(header, indent=4), file=f)
        print(F"{fn} written")

import json

from app.services import jwt
from app.models.domain.users import User


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
    email = auth_info['email']
    account = auth_info['account']
    test_user = User(email=email, accounts=account, is_zonar=False)
    token = jwt.create_access_token_for_user(test_user, "Zonar!") 
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
    import json

    email = sys.argv[1]
    account_code = sys.argv[2]
    header = make_onroute_auth_header({'email': email, 'account': account_code})

    fn = F"{account_code}.{email}.auth_header.json"
    with open(fn, "w") as f:
        print(json.dumps(header, indent=4), file=f)
        print(F"{fn} written")
    

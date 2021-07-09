import datetime as dt
from typing import Dict
import jwt


def create_jwt_token(
        *,                      # kwargs only
        jwt_content: Dict[str, str],
        jwt_subject: str,
        secret_key: str,
        expires_delta: dt.timedelta,
        algorithm: str='HS256'
) -> str:
    """ Create a JWT, currently used in testing, but could be used for the app itself """
    to_encode = jwt_content.copy()
    expire = dt.datetime.utcnow() + expires_delta
    to_encode.update(dict(exp=expire, sub=jwt_subject))
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


if __name__ == '__main__':
    import sys
    import json

    def create_onroute_jwt(email="victor@testenv.com",
                           account="dbr47_rep1023",
                           jwt_subject='access',
                           secret_key='Zonar!',
                           algorithm='HS256',
                           expires_in_mins=10090):  # one week
        content = {
            "email": email,
            "account": account,
            "is_zonar": True,
        }
        expires = dt.timedelta(minutes=expires_in_mins)
        token = create_jwt_token(jwt_content=content,
                                 jwt_subject=jwt_subject,
                                 secret_key=secret_key,
                                 expires_delta=expires)

        print(token)

    def decode(token, secret='Zonar!', algorithm='HS256'):
        print(json.dumps(jwt.decode(token, secret, algorithm), indent=4))

    cmd = sys.argv[1]
    args = sys.argv[2:]
    method = locals()[cmd]
    method(*args)

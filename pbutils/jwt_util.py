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

    def test_create_jwt_token():
        content = {
            "email": "victor@testenv.com",
            "account": "dbr47_rep1023"
        }
        expires = dt.timedelta(minutes=60)
        secret_key = 'some secret'
        token = create_jwt_token(jwt_content=content,
                                 jwt_subject='some subject',
                                 secret_key=secret_key,
                                 expires_delta=expires)

        content_dec = jwt.decode(token, secret_key)
        print(json.dumps(content_dec, indent=4))

    def decode(token, secret='Zonar!', algorithm='HS256'):
        print(json.dumps(jwt.decode(token, secret, algorithm), indent=4))

    cmd = sys.argv[1]
    args = sys.argv[2:]
    method = locals()[cmd]
    method(*args)

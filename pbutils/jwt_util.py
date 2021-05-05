import datetime as dt
from typing import Dict
import jwt as standard_jwt


def create_jwt_token(
        *,                      # kwargs only
        jwt_content: Dict[str, str],
        jwt_subject: str='access',
        secret_key: str,
        expires_delta: dt.timedelta,
        algorithm: str='HS256',
) -> str:
    """ Create a JWT, currently used in testing, but could be used for the app itself """
    to_encode = jwt_content.copy()
    expire = dt.datetime.utcnow() + expires_delta
    to_encode.update(dict(exp=expire, sub=jwt_subject))
    return standard_jwt.encode(to_encode, secret_key, algorithm=algorithm)


if __name__ == '__main__':
    import sys
    import json

    with open(sys.argv[1]) as data_stream:
        jwt_content = json.load(data_stream)

    secret_key = sys.argv[2]
    delta = {sys.argv[4]: int(sys.argv[3])}  # eg 60 "minutes"
    expires_delta = dt.timedelta(**delta)
    enc_token = create_jwt_token(jwt_content=jwt_content, secret_key=secret_key, expires_delta=expires_delta)
    print(enc_token)

    token = standard_jwt.decode(enc_token, secret_key, "HS256")
    print(F"token: {json.dumps(token, indent=4)}")

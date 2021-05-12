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

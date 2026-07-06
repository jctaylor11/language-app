from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWSError

from backend.config import JOSE_SECRET_KEY, JOSE_ALGORITHM, ACCESS_TOKEN_EXPIRES_MINUTES

def create_access_token(user_id, access_token_expiry_minutes = ACCESS_TOKEN_EXPIRES_MINUTES):
    encode = {'id': user_id}
    expires_delta = timedelta(minutes=int(access_token_expiry_minutes))
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})

    try:
        return jwt.encode(encode, JOSE_SECRET_KEY, JOSE_ALGORITHM)
    except JWSError as e:
        raise RuntimeError(f"Failed to sign access token — check SECRET_KEY/ALGORITHM config: {e}") from e
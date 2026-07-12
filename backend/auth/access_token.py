from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWTError, JWSError
from fastapi import HTTPException, status, Request

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
    
def decode_access_token(request: Request):
    token = request.cookies.get("access_token")

    if token is None:   # For non-existent access token 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No access token')

    try:    # For malformed access tokens
        payload = jwt.decode(token, JOSE_SECRET_KEY, algorithms=[JOSE_ALGORITHM])
        user_id = payload.get('id')
        
        if user_id is None: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

        return user_id
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

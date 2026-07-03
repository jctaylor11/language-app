from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from backend.auth.google import get_user_infos_from_google_token
from backend.schemas import GoogleToken

router = APIRouter()


@router.post('/auth-google')
async def auth_google(google_token: GoogleToken):
    credential = google_token.credential
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No credential provided'
        )
    
    check = get_user_infos_from_google_token(credential)

    if check['status'] is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )
    
    user_infos = check['user_infos']

    # Check if user exists, if not create user, if so generate the JWT token

    # As a placholder, it just returns the email of the user that logged in to confirm logic. Will be replaced with JWT
    return {"token": user_infos["email"]}
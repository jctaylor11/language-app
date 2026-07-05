from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from typing import Annotated
from sqlalchemy import Connection

from backend.auth.google import get_user_infos_from_google_token
from backend.auth.users import get_or_create_user_id
from backend.schemas import GoogleToken
from backend.db.connection import get_write_connection

router = APIRouter()


@router.post('/auth-google')
async def auth_google(google_token: GoogleToken, conn: Annotated[Connection, Depends(get_write_connection)]):
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

    user_id = get_or_create_user_id(conn, user_infos)

    # TODO:
    # jwt = create_access_token(user_id) -> str

    # As a placholder, it just returns the email of the user that logged in to confirm logic. Will be replaced with JWT
    return {"token": user_infos["email"]}

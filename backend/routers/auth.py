from fastapi import APIRouter, HTTPException, status, Depends, Response
from typing import Annotated
from sqlalchemy import Connection

from backend.auth.google import get_user_infos_from_google_token
from backend.auth.users import get_or_create_user_id
from backend.auth.access_token import create_access_token, decode_access_token
from backend.schemas import GoogleToken
from backend.db.connection import get_write_connection

router = APIRouter()


@router.post('/auth-google')
async def auth_google(google_token: GoogleToken, response: Response, conn: Annotated[Connection, Depends(get_write_connection)]):
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

    jwt = create_access_token(user_id)

    response.set_cookie("access_token", jwt, httponly=True)

    return {"status": "ok"}


@router.get('/auth/me')
async def auth_check(user_id: Annotated[int, Depends(decode_access_token)]):
    return {"authenticated": True}  # Only returns true if jwt successfully decoded, hence auth check returns true

@router.post('/auth/logout')
async def auth_logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}

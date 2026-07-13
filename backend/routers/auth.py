from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from typing import Annotated
from sqlalchemy import Connection

from backend.auth.google import get_user_infos_from_google_token
from backend.auth.users import get_or_create_user_id
from backend.auth.access_token import create_access_token, decode_access_token
from backend.auth.refresh_token import create_refresh_token, get_user_id_from_valid_refresh_token, delete_refresh_token
from backend.schemas import GoogleToken
from backend.db.connection import get_write_connection
from backend.config import REFRESH_TOKEN_EXPIRES_DAYS

router = APIRouter()


def set_auth_cookies(response: Response, conn: Connection, user_id: int) -> None:
    jwt = create_access_token(user_id)
    refresh_token = create_refresh_token(conn, user_id)

    response.set_cookie("access_token", jwt, httponly=True)
    # path to auth/refresh to limit scope to only place that uses it. max_age makes it persist browser restarts
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        path="/auth/refresh",
        max_age=int(REFRESH_TOKEN_EXPIRES_DAYS) * 24 * 60 * 60,
    )


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

    set_auth_cookies(response, conn, user_id)

    return {"status": "ok"}


@router.get('/auth/me')
async def auth_check(user_id: Annotated[int, Depends(decode_access_token)]):
    return {"authenticated": True}  # Only returns true if jwt successfully decoded, hence auth check returns true

@router.post('/auth/logout')
async def auth_logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok"}


@router.post('/auth/refresh')
async def auth_refresh(request: Request, response: Response, conn: Annotated[Connection, Depends(get_write_connection)]):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='No refresh token')

    user_id = get_user_id_from_valid_refresh_token(conn, refresh_token)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired refresh token')

    delete_refresh_token(conn, refresh_token)   # Rotate token - single use so stolen token only gives a single access
    set_auth_cookies(response, conn, user_id)

    return {"status": "ok"}

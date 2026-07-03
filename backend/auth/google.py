from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend.config import OIDC_GOOGLE_CLIENT_ID

def get_user_infos_from_google_token(id_token_str):
    try:
        id_token_info = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            OIDC_GOOGLE_CLIENT_ID
        )
    except ValueError:
        return {
            'status': False,
            'user_infos': None
        }

    user_infos = {
        'id': id_token_info['sub'],
        'email': id_token_info['email']
    }

    return {
        'status': True,
        'user_infos': user_infos
    }
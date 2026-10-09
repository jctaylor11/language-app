import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']  # environ instead of getenv to raise KeyError if not set
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL') # getenv since it's not required in production - missing test url will cause it to fail
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"  # optional, defaults to off

OIDC_GOOGLE_CLIENT_ID = os.getenv('OIDC_GOOGLE_CLIENT_ID')

JOSE_SECRET_KEY = os.getenv('JOSE_SECRET_KEY')
JOSE_ALGORITHM = os.getenv('JOSE_ALGORITHM')
ACCESS_TOKEN_EXPIRES_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRES_MINUTES')
REFRESH_TOKEN_EXPIRES_DAYS = os.getenv('REFRESH_TOKEN_EXPIRES_DAYS')
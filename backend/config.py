import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
TEST_DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('TEST_DB_NAME')}"
OIDC_GOOGLE_CLIENT_ID = os.getenv('OIDC_GOOGLE_CLIENT_ID')

JOSE_SECRET_KEY = os.getenv('JOSE_SECRET_KEY')
JOSE_ALGORITHM = os.getenv('JOSE_ALGORITHM')
ACCESS_TOKEN_EXPIRES_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRES_MINUTES')
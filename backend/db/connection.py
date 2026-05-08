import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


def get_engine():
    """Create and return SQLAlchemy engine using env variables"""
    load_dotenv()   # TODO: Move to caller

    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')
    port = os.getenv('DB_PORT')

    try:
        # From sqlalchemy docs: database url = dialect+driver://username:password@host:port/database
        engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}", echo=True)
        with engine.connect():  # Tests the connection
            pass
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")
        
    return engine
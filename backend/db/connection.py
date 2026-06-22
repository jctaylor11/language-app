from sqlalchemy import create_engine



from backend.config import DATABASE_URL

def get_engine():
    """Create and return SQLAlchemy engine"""
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        with engine.connect():  # Tests the connection
            pass
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")
        
    return engine

engine = get_engine()

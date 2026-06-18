from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # reconnect on stale connections
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,  # SQL logging in dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db  #it is used in the routes to get a db session and perform operations on the database. 
        #The yield statement allows the function to return a value (the db session) and then continue executing code after the yield when the caller is done with the session. This is useful for ensuring that the database session is properly closed after use, even if an error occurs during database operations.
    
    finally:
        db.close()

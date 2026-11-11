
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.models.entities import Base

# Import event models so all 10 tables are registered
from src.models.events import (
    ContactPreference,
    CollectionCase,
    ContactAttempt,
    PromiseToPay,
    Payment,
)


# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


# Enable foreign key enforcement in SQLite
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def create_database():
    """Create all 10 database tables."""
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Database created!")
    print("Total tables:", len(Base.metadata.tables))


def get_db():
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

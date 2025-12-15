from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Create the database engine
engine = create_engine(
    settings.neon_database_url,
    pool_pre_ping=True,  # Verify connections are alive before using them
    pool_recycle=300,    # Recycle connections every 5 minutes
)

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency function to get a database session.
    This is meant to be used with FastAPI's dependency injection system.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    This should be called when starting the application.
    """
    logger.info("Initializing database and creating tables if they don't exist")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete")


def get_db_health() -> bool:
    """
    Check if the database is accessible.
    
    Returns:
        True if the database is accessible, False otherwise
    """
    try:
        with SessionLocal() as db:
            # Perform a simple query to test the connection
            db.execute("SELECT 1")
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


# Initialize database when module is loaded
if settings.neon_database_url:
    init_db()
else:
    logger.warning("No database URL provided. Database will not be initialized.")
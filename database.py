import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# For MySQL connections, ensure we're using the correct driver
if "mysql" not in DATABASE_URL:
    logger.warning(
        "DATABASE_URL doesn't contain 'mysql'. "
        "Make sure you're using a MySQL connection string like: "
        "mysql+aiomysql://user:password@localhost:3306/bidding_engine"
    )

# Create SQLAlchemy engine with MySQL-specific connection pooling settings
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=300,  # Recycle connections after 5 minutes (important for MySQL)
    pool_pre_ping=True,  # Check connection validity before using it
    # MySQL-specific settings
    connect_args={
        "charset": "utf8mb4",  # Support for full UTF-8 character set
        "use_unicode": True
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

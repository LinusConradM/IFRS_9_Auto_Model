import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Construct the database URL
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

# Determine if full database configuration is present
_required = [
    'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST',
    'POSTGRES_PORT', 'POSTGRES_DB'
]
_has_db_env = all(os.getenv(var) for var in _required)

# Skip engine/session creation during Alembic migrations or if DB env is incomplete
if os.getenv('ALEMBIC') == '1' or not _has_db_env:
    engine = None
    SessionLocal = None
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.getenv('SQLALCHEMY_POOL_SIZE', 10)),
        max_overflow=int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 20)),
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()
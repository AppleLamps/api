from sqlalchemy import Column, String, DateTime, Integer, Boolean, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import os
import secrets

Base = declarative_base()

class APIKey(Base):
    """API Key model for tracking user access"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    user_name = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    rate_limit = Column(Integer, default=10)  # requests per minute
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<APIKey(user={self.user_name}, active={self.is_active})>"


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grokipedia_api.db")

# Use different pool configuration based on database type
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL or MySQL
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def create_api_key(user_name: str, user_email: str, rate_limit: int = 10, notes: str = None) -> str:
    """Create a new API key and store it in database"""
    key = f"grok_{secrets.token_urlsafe(32)}"
    
    db = SessionLocal()
    try:
        api_key = APIKey(
            key=key,
            user_name=user_name,
            user_email=user_email,
            rate_limit=rate_limit,
            notes=notes
        )
        db.add(api_key)
        db.commit()
        return key
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_api_key_record(db, key: str) -> APIKey | None:
    """Get API key record from database"""
    return db.query(APIKey).filter(APIKey.key == key, APIKey.is_active == True).first()


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key"""
    db = SessionLocal()
    try:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            return False
        api_key.is_active = False
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_all_api_keys(active_only: bool = True) -> list[APIKey]:
    """Get all API keys"""
    db = SessionLocal()
    try:
        query = db.query(APIKey)
        if active_only:
            query = query.filter(APIKey.is_active == True)
        return query.all()
    finally:
        db.close()


def update_api_key_usage(key: str):
    """Update last_used timestamp for an API key"""
    db = SessionLocal()
    try:
        api_key = db.query(APIKey).filter(APIKey.key == key).first()
        if api_key:
            api_key.last_used = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import get_settings
import os

settings = get_settings()

# Garantiza que el directorio existe
db_path = settings.database_url.replace("sqlite:////", "/").replace("sqlite:///", "")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import User, DeviceSnapshot, DailyScore, UserDevice, PushToken  # noqa
    Base.metadata.create_all(bind=engine)

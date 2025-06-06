from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.config.settings import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

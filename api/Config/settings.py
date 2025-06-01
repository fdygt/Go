import os

ENV = os.getenv("ENV", "development")

class BaseConfig:
    DEBUG = False
    DATABASE_URL = "sqlite:///default.db"
    SECRET_KEY = "your-default-secret"

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = "sqlite:///dev.db"

class ProductionConfig(BaseConfig):
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    SECRET_KEY = os.getenv("SECRET_KEY")

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}.get(ENV, DevelopmentConfig)

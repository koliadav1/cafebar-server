from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD")

    HASH_SECRET_KEY = os.getenv("HASH_SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    YANDEX_ACCESS_KEY=os.getenv("YANDEX_ACCESS_KEY")
    YANDEX_SECRET_KEY=os.getenv("YANDEX_SECRET_KEY")
    YANDEX_BUCKET_NAME=os.getenv("YANDEX_BUCKET_NAME")
    YANDEX_ENDPOINT=os.getenv("YANDEX_ENDPOINT")

    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    @classmethod
    def validate(cls):
        if not cls.DATABASE_URL:
            raise ValueError('DATABASE_URL не найден в .env')
        if not cls.SWAGGER_PASSWORD:
            raise ValueError('SWAGGER_PASSWORD не найден в .env')
        if not cls.HASH_SECRET_KEY:
            raise ValueError('HASH_SECRET_KEY не найден в .env')
        if not cls.ALGORITHM:
            raise ValueError('ALGORITHM не найден в .env')
        if not cls.ACCESS_TOKEN_EXPIRE_MINUTES:
            raise ValueError('ACCESS_TOKEN_EXPIRE_MINUTES не найден в .env')
        if not cls.YANDEX_ACCESS_KEY:
            raise ValueError('YANDEX_ACCESS_KEY не найден в .env')
        if not cls.YANDEX_SECRET_KEY:
            raise ValueError('YANDEX_SECRET_KEY не найден в .env')
        if not cls.YANDEX_BUCKET_NAME:
            raise ValueError('YANDEX_BUCKET_NAME не найден в .env')
        if not cls.YANDEX_ENDPOINT:
            raise ValueError('YANDEX_ENDPOINT не найден в .env')

Config.validate()
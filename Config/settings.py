from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST:str
    DB_PORT:int
    DB_USER:str
    DB_PASSWORD:str
    DB_NAME:str

    REDIS_HOST:str
    REDIS_PORT:int
    REDIS_DB:int

    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_ENDPOINT: str
    OSS_BUCKET_NAME: str

    SMTP_SERVER: str
    SMTP_PORT: int
    SENDER: str
    AUTH_CODE: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    REFRESH_TOKEN_EXPIRE_DAYS: int

    HASH_SALT:str


    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings=Settings()
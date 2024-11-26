from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN: str
    LOGGING_LEVEL: str
    POSTGRES_USER: str
    POSTGRES_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: str

    def get_db_url(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_NAME}'

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()

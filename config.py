from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLOUDFLARE_ACCOUNT_ID: str
    CLOUDFLARE_API_TOKEN: str

    class Config:
        env_file = ".env"

settings = Settings()

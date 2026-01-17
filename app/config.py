from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    rapidapi_key: str 
    rapidapi_host: str


settings = Settings()
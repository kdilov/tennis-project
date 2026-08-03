from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    rapidapi_key: str
    rapidapi_host: str

    # Which upstream serves /rankings. Defaults to the existing provider, so
    # leaving every setting below unset changes nothing.
    rankings_provider: str = "rapidapi"

    # Only read when rankings_provider == "livetennisapi".
    livetennisapi_key: str | None = None
    livetennisapi_base_url: str = "https://api.livetennisapi.com/api/public/v1"
    livetennisapi_system: str = "atp"
    livetennisapi_limit: int = 50


settings = Settings()
import requests
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataJudSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(validation_alias="DATAJUD_API_KEY")
    url: str = "https://api-publica.datajud.cnj.jus.br"


class DataJudClient:

    def __init__(self, settings: DataJudSettings) -> None:
        self.url = settings.url.rstrip("/")
        self.headers = {
            "Authorization": f"APIKey {settings.api_key.get_secret_value()}"
        }

    def ingest(self, tribunal: str, body: dict) -> dict:
        response = requests.post(
            f"{self.url}/{tribunal}/_search",
            json=body,
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

import requests
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type


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

    # Configuração de retry: Tenta até 5 vezes, esperando um tempo exponencial (entre 4s e 15s) entre tentativas
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=15),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True
    )
    def ingest(self, tribunal: str, body: dict) -> dict:
        response = requests.post(
            f"{self.url}/{tribunal}/_search",
            json=body,
            headers=self.headers,
            timeout=90,  # Aumentado de 30 para 90 segundos devido à lentidão comum do DataJud
        )
        response.raise_for_status()
        return response.json()

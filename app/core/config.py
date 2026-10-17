from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    database_url: str
    admin_username: str | None = None
    admin_password: SecretStr | None = None
    secret_key: SecretStr = SecretStr("local-development-key-change-before-production")
    environment: Literal["development", "test", "production"] = "development"
    public_base_url: HttpUrl = HttpUrl("http://localhost:8000")
    upload_dir: Path = Path("uploads")
    business_timezone: str = "America/Fortaleza"

    @model_validator(mode="after")
    def production_settings(self):
        from zoneinfo import ZoneInfo

        ZoneInfo(self.business_timezone)
        if (
            self.public_base_url.username
            or self.public_base_url.password
            or self.public_base_url.path not in {None, "/"}
            or self.public_base_url.query
            or self.public_base_url.fragment
        ):
            raise ValueError("PUBLIC_BASE_URL deve conter apenas protocolo, host e porta.")
        if self.environment == "production":
            secret = self.secret_key.get_secret_value()
            if len(secret) < 32 or secret.startswith(("local-development", "SUBSTITUA")):
                raise ValueError("SECRET_KEY forte e exclusiva é obrigatória em produção.")
            if not self.admin_username or not self.admin_password:
                raise ValueError("Credenciais administrativas obrigatórias em produção.")
            if len(
                self.admin_password.get_secret_value()
            ) < 16 or self.admin_password.get_secret_value().startswith("SUBSTITUA"):
                raise ValueError("ADMIN_PASSWORD deve ter pelo menos 16 caracteres em produção.")
            if self.public_base_url.scheme != "https":
                raise ValueError("PUBLIC_BASE_URL deve usar HTTPS em produção.")
        return self

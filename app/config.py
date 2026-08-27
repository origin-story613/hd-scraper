from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./deals.db"
    hd_zip_codes: str = "10001"
    request_delay_seconds: float = 3.0
    headless: bool = True
    min_discount_percent: int = 20
    log_level: str = "INFO"

    @property
    def zip_code_list(self) -> list[str]:
        return [z.strip() for z in self.hd_zip_codes.split(",") if z.strip()]


settings = Settings()

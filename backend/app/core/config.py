from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://tb_user:pass@localhost:5432/tb_testing"
    keycloak_url: str = ""
    keycloak_realm: str = ""
    keycloak_client_id: str = "tb-testing-app"
    keycloak_backend_client_id: str = "tb-testing-backend"
    keycloak_backend_client_secret: str = ""
    wfm_base_url: str = "https://10.6.4.118:6021/api/wfm-shift-be/v1.0"
    wfm_verify_ssl: bool = False
    test_pass_threshold: int = 70
    test_timer_seconds: int = 1800
    test_min_questions: int = 5
    timezone: str = "Asia/Almaty"

    @property
    def keycloak_jwks_uri(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_token_uri(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/token"


settings = Settings()

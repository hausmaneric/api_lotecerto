from dataclasses import dataclass
import os


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = _get_env("LOTECERTO_APP_NAME", "LoteCerto API")
    api_prefix: str = _get_env("LOTECERTO_API_PREFIX", "/api/v1")
    database_url: str = _get_env("LOTECERTO_DATABASE_URL", "sqlite:///./lotecerto_api.db")
    secret_key: str = _get_env("LOTECERTO_SECRET_KEY", "troque-esta-chave-em-producao")
    access_token_expire_minutes: int = int(
        _get_env("LOTECERTO_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    default_admin_username: str = _get_env("LOTECERTO_DEFAULT_ADMIN_USERNAME", "admin")
    default_admin_password: str = _get_env("LOTECERTO_DEFAULT_ADMIN_PASSWORD", "123456")


settings = Settings()

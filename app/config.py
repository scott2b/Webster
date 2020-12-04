import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator, ValidationError, AnyUrl


class Settings(BaseSettings):
    DEBUG: bool = False
    MOCK_CLASSIFIERS: bool = False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    CSRF_KEY: str = secrets.token_urlsafe(32)
    SESSION_COOKIE: str = 'session'
    SESSION_EXPIRE_SECONDS: int = 60 * 60 * 24 * 10
    SESSION_SAME_SITE: str = 'lax' # lax, strict, or none
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 60 * 24 * 8
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    ALLOWED_HOSTS: List[str]
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ['http://localhost:8080']

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str

    # TODO: Create a validator for this. Pydantic provides a PostgresDsn, but
    # not other DSN types. We want to at least support sqlite here, so just
    # making this a non-validated string for now.
    SQLALCHEMY_DATABASE_URI: str = None

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # OAUTH
    OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS: int = 30 # 300
    OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS: int = 600

    @validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values["PROJECT_NAME"]
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "templates/email"
    EMAILS_ENABLED: bool = False

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    USERS_OPEN_REGISTRATION: bool = False
    DOCSET: str = 'full' # some docs are flagged only to show in full mode

    class Config:
        #env_file = '.env'
        case_sensitive = False # Has no effect on Windows ∴ not recommended
        env_prefix = 'WEBSTER_'


settings = Settings()

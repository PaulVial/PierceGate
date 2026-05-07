from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    litellm_url: str = "http://litellm:8000"
    litellm_master_key: str
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_from_email: str = ""
    slack_webhook_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

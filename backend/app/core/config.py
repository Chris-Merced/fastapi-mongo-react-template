"""
App configuration, loaded once at import time.

pydantic-settings reads from environment variables (and a local .env file,
if present) and validates them against the types declared below - the
Python equivalent of parsing `process.env` through a zod schema, except
it's a first-class library pattern here rather than something you bolt on.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -- Mongo --
    mongodb_uri: str
    mongodb_db_name: str = "acme_teams"

    # -- Auth --
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # -- App --
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we only parse/validate the environment once per process.

    @lru_cache is a decorator (Python's version of wrapping a function to
    memoize its return value) - first call does the work, every later call
    with the same args returns the cached result instantly.
    """
    return Settings()

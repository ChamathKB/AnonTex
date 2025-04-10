import logging
import os

TARGET = os.getenv("TARGET", "https://api.openai.com")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ENTITY_TTL = os.getenv("ENTITY_TTL", 600)
ENTITY_LIST = ["PHONE_NUMBER", "PERSON", "EMAIL_ADDRESS", "LOCATION", "ORGANIZATION", "CREDIT_CARD"]
DEFAULT_CONFIG_PATH = os.getenv("DEFAULT_CONFIG_PATH", "anontex/languages-config.yml")
LANGUAGE = os.getenv("LANGUAGE", "en")
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

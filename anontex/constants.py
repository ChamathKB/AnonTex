import os

TARGET = "https://api.openai.com"  # Target server
ENTITY_TTL = 600  # 10 minutes
ENTITY_LIST = ["PHONE_NUMBER", "PERSON", "EMAIL_ADDRESS", "LOCATION", "ORGANIZATION", "CREDIT_CARD"]
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEFAULT_CONFIG_PATH = os.getenv("DEFAULT_CONFIG_PATH", "anontex/languages-config.yml")

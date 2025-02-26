import os

TARGET = "https://api.openai.com"  # Target server
ENTITY_TTL = 600  # 10 minutes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost")

import json
from typing import Any
from uuid import uuid4

from faker import Faker
from fastapi import HTTPException, Request

from anontex.constants import ENTITY_TTL

fake_generator = Faker()


async def anonymize_text(
    request: Request, app: Any, entities: list[str] | None, language: str = "en"
) -> tuple[str, str]:
    """Anonymize message using Presidio Analyzer and Anonymizer with Faker-generated placeholders."""
    analyzer = app.state.analyzer
    # anonymizer = app.state.anonymizer
    redis_client = app.state.redis_client
    message = json.loads(await request.body())["messages"][-1]["content"]

    # Analyze text using Presidio Analyzer
    results = analyzer.analyze(text=message, entities=entities, language=language)

    fake_mapping: dict[str, str] = {}  # Mapping between fake and original values
    anonymized_message: str = message  # Start with the original message

    for entity in sorted(results, key=lambda e: e.start, reverse=True):
        original_value = message[entity.start : entity.end]

        # Generate a fake replacement based on the entity type
        if entity.entity_type == "PERSON":
            fake_value = fake_generator.name()
        elif entity.entity_type == "ORGANIZATION":
            fake_value = fake_generator.company()
        elif entity.entity_type == "EMAIL_ADDRESS":
            fake_value = fake_generator.email()
        elif entity.entity_type == "PHONE_NUMBER":
            fake_value = fake_generator.phone_number()
        elif entity.entity_type == "LOCATION":
            fake_value = fake_generator.city()
        else:
            fake_value = fake_generator.word()

        # Store mapping of fake to original value
        fake_mapping[fake_value] = original_value

        # Replace the original entity with the fake value in the anonymized text
        anonymized_message = anonymized_message[: entity.start] + fake_value + anonymized_message[entity.end :]

    # Store fake-to-original mapping in Redis
    request_id = str(uuid4())
    await redis_client.setex(f"entity:{request_id}", ENTITY_TTL, json.dumps(fake_mapping))

    return anonymized_message, request_id


async def deanonymize_text(anonymized_message: str, app: Any, request_id: str) -> str:
    """Deanonymize text using stored fake-to-original mapping from Redis."""
    redis_client = app.state.redis_client

    # Retrieve the mapping from Redis
    fake_mapping_json = await redis_client.get(f"entity:{request_id}")
    if not fake_mapping_json:
        raise HTTPException(status_code=404, detail="Request ID not found or expired")

    fake_mapping: dict[str, str] = json.loads(fake_mapping_json)

    # Replace fake values with original values
    deanonymized_message: str = anonymized_message
    for fake_value, original_value in fake_mapping.items():
        deanonymized_message = deanonymized_message.replace(fake_value, original_value)

    # Optionally, delete mapping after use
    await redis_client.delete(f"entity:{request_id}")

    return deanonymized_message

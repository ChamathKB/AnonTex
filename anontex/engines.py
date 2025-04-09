import json
import logging
import re
from uuid import uuid4

from faker import Faker
from fastapi import FastAPI, Request

from anontex.constants import ENTITY_TTL
from anontex.exceptions import RequestIDError

fake_generator = Faker()


def _normalize_subcomponents(message: str, fake_mapping: dict[str, str]) -> str:
    """Ensure all components of fake values are restored to the full fake value."""
    for full_fake_value in sorted(fake_mapping.keys(), key=lambda x: -len(x)):
        components = full_fake_value.split()

        for comp in components:
            # Escape for regex safety
            escaped_comp = re.escape(comp)

            # Use word-boundary to avoid partial word matches
            pattern = rf"\b{escaped_comp}\b"

            # Only replace if component is not already part of full fake
            def repl(match):
                matched_word = match.group(0)
                if matched_word != full_fake_value and full_fake_value not in message:
                    logging.debug(f"🧩 Normalizing component '{matched_word}' → '{full_fake_value}'")
                    return full_fake_value
                return matched_word

            message = re.sub(pattern, repl, message)

    return message


async def anonymize_text(
    request: Request, app: FastAPI, entities: list[str] | None, language: str = "en"
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
        elif entity.entity_type == "CREDIT_CARD":
            fake_value = fake_generator.credit_card_number()
        else:
            fake_value = fake_generator.word()

        # Store mapping of fake to original value
        fake_mapping[fake_value] = original_value
        logging.debug(f"🔍️ Anonymizing {entity.entity_type}: {original_value} -> {fake_value}")

        # Replace the original entity with the fake value in the anonymized text
        anonymized_message = anonymized_message[: entity.start] + fake_value + anonymized_message[entity.end :]

    # Store fake-to-original mapping in Redis
    request_id = str(uuid4())
    await redis_client.setex(f"entity:{request_id}", ENTITY_TTL, json.dumps(fake_mapping))

    return anonymized_message, request_id


async def deanonymize_text(anonymized_message: str, app: FastAPI, request_id: str) -> str:
    """Deanonymize text using stored fake-to-original mapping from Redis."""
    redis_client = app.state.redis_client

    # Retrieve the mapping from Redis
    fake_mapping_json = await redis_client.get(f"entity:{request_id}")
    if not fake_mapping_json:
        raise RequestIDError(f"Request ID {request_id} not found in Redis")

    fake_mapping: dict[str, str] = json.loads(fake_mapping_json)
    logging.debug(f"🔍️ Deanonymizing {fake_mapping}")

    # Replace fake values with original values
    message = _normalize_subcomponents(anonymized_message, fake_mapping)

    # Step 2: Replace full fake values with original ones
    for fake_value, original_value in sorted(fake_mapping.items(), key=lambda x: -len(x[0])):
        logging.debug(f"🔁 Replacing '{fake_value}' → '{original_value}'")
        escaped_fake = re.escape(fake_value)
        pattern = rf"\b{escaped_fake}\b"
        message = re.sub(pattern, original_value, message)

    await redis_client.delete(f"entity:{request_id}")

    return message

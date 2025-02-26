import json
from uuid import uuid4

from fastapi import HTTPException

from anontex.constants import ENTITY_TTL


async def anonymize_text(request, app, entities=None, language="en"):
    """Anonymize message using Presidio Analyzer and Anonymizer."""

    analyzer = app.state.analyzer
    anonymizer = app.state.anonymizer
    redis_client = app.state.redis_client
    message = json.loads(await request.body())["messages"][-1]["content"]
    results = analyzer.analyze(text=message, entities=entities, language=language)

    # Anonymize detected entities
    anonymized_result = anonymizer.anonymize(text=message, analyzer_results=results)
    anonymized_message = anonymized_result.text

    entity_mapping = {entity.start: (entity.entity_type, message[entity.start : entity.end]) for entity in results}
    request_id = str(uuid4())
    await redis_client.setex(f"entity:{request_id}", ENTITY_TTL, json.dumps(entity_mapping))

    return anonymized_message, request_id


async def deanonymize_text(anonymized_message, app, request_id):
    """Deanonymize text using stored entity mapping from Redis."""

    # Retrieve initialized Redis instance
    redis_client = app.state.redis_client

    # Retrieve entity mapping from Redis
    entity_mapping_json = await redis_client.get(f"entity:{request_id}")
    if not entity_mapping_json:
        raise HTTPException(status_code=404, detail="Request ID not found or expired")

    entity_mapping = json.loads(entity_mapping_json)

    # Replace placeholders with original values
    deanonymized_text = anonymized_message
    for start, (entity_type, original_value) in sorted(entity_mapping.items(), reverse=True):
        anonymized_placeholder = f"[{entity_type}]"
        deanonymized_message = deanonymized_text.replace(anonymized_placeholder, original_value, 1)

    # Optionally, delete entity mapping after use
    await redis_client.delete(f"entity:{request_id}")

    return deanonymized_message

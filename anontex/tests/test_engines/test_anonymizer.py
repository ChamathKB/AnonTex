import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from anontex.engines import anonymize_text


@pytest.mark.asyncio
async def test_anonymize_text():

    # Fake message body
    body_content = {"messages": [{"content": "Hello, my name is John Doe and I work at OpenAI."}]}

    # Mock Request
    mock_request = MagicMock()
    mock_request.body = AsyncMock(return_value=json.dumps(body_content).encode())

    # Mock EntityResult
    class MockEntity:
        def __init__(self, start, end, entity_type):
            self.start = start
            self.end = end
            self.entity_type = entity_type

    mock_entities = [
        MockEntity(start=18, end=26, entity_type="PERSON"),  # "John Doe"
        MockEntity(start=41, end=47, entity_type="ORGANIZATION"),  # "OpenAI"
    ]

    # Mock analyzer
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = mock_entities

    # Mock redis client
    mock_redis_client = AsyncMock()

    # Mock app.state
    mock_app = MagicMock()
    mock_app.state.analyzer = mock_analyzer
    mock_app.state.redis_client = mock_redis_client

    anonymized_message, request_id = await anonymize_text(mock_request, mock_app, entities=["PERSON", "ORGANIZATION"])

    assert "John Doe" not in anonymized_message
    assert "OpenAI" not in anonymized_message

    # Check Redis called correctly
    mock_redis_client.setex.assert_awaited_once()
    args, kwargs = mock_redis_client.setex.call_args
    redis_key = args[0]
    redis_value = json.loads(args[2])

    assert redis_key.startswith("entity:")
    assert isinstance(redis_value, dict)
    assert any(orig == "John Doe" for orig in redis_value.values())
    assert any(orig == "OpenAI" for orig in redis_value.values())

    # Check request_id is non-empty
    assert isinstance(request_id, str)
    assert len(request_id) > 0

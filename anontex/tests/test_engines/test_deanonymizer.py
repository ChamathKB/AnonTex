import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from anontex.engines import deanonymize_text


@pytest.mark.asyncio
async def test_deanonymize_text():
    anonymized_message = "Test Name works at Test Company and lives in Test City."
    request_id = "fake_request_id"

    # Fake mapping in Redis
    fake_mapping = {"Test Name": "John Doe", "Test Company": "OpenAI", "Test City": "New York"}

    # Mock Redis client
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = json.dumps(fake_mapping)
    mock_redis_client.delete = AsyncMock()

    # Mock app.state
    mock_app = MagicMock()
    mock_app.state.redis_client = mock_redis_client

    deanonymized_message = await deanonymize_text(anonymized_message, mock_app, request_id)

    assert deanonymized_message == "John Doe works at OpenAI and lives in New York."
    mock_redis_client.get.assert_awaited_once_with(f"entity:{request_id}")
    mock_redis_client.delete.assert_awaited_once_with(f"entity:{request_id}")

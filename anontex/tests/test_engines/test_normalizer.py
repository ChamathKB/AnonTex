import pytest

from anontex.engines import _normalize_subcomponents


@pytest.mark.parametrize(
    "message, fake_mapping, expected",
    [
        # Basic normalization
        ("John went to the market", {"John Doe": "Johnny Bravo"}, "John Doe went to the market"),
        # Full value already present
        ("John Doe went to the market", {"John Doe": "Johnny Bravo"}, "John Doe went to the market"),
        # No matching components
        ("Alice went to the market", {"John Doe": "Johnny Bravo"}, "Alice went to the market"),
        # Multiple mappings
        ("John and Jane met", {"John Doe": "Johnny Bravo", "Jane Doe": "Jahnny Alpha"}, "John Doe and Jane Doe met"),
    ],
)
def test_normalize_subcomponents(message, fake_mapping, expected):
    assert _normalize_subcomponents(message, fake_mapping) == expected

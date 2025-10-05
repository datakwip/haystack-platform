"""
Test utility functions and helpers.
"""

from faker import Faker
from datetime import datetime, timedelta
from typing import List, Dict, Any

fake = Faker()


def create_test_entity_payload(org_id: int) -> Dict[str, Any]:
    """
    Generate test entity creation payload.

    Args:
        org_id: Organization ID

    Returns:
        Entity creation payload
    """
    return {
        "org_id": org_id,
        "tags": [
            {"tag_name": "site", "value_s": fake.company()},
            {"tag_name": "area", "value_n": fake.random_int(1000, 100000)}
        ]
    }


def create_test_tag_def_payload(org_id: int, name: str = None) -> Dict[str, Any]:
    """
    Generate test tag definition payload.

    Args:
        org_id: Organization ID
        name: Tag name (auto-generated if None)

    Returns:
        Tag definition creation payload
    """
    if name is None:
        name = f"test_{fake.word()}"

    return {
        "name": name,
        "org_id": org_id,
        "metas": [
            {
                "attribute": "lib",
                "value": "ph"  # Default library value
            }
        ],
        "enums": None  # Optional field
    }


def create_test_value_payload(entity_id: int, org_id: int, value: float = None) -> Dict[str, Any]:
    """
    Generate test value payload.

    Args:
        entity_id: Entity ID
        org_id: Organization ID
        value: Value (random if None)

    Returns:
        Value creation payload
    """
    if value is None:
        value = fake.random.uniform(60.0, 80.0)

    return {
        "entity_id": entity_id,
        "org_id": org_id,
        "timestamp": datetime.now().isoformat(),
        "value": value
    }


def create_test_values_bulk(
    entity_id: int,
    org_id: int,
    count: int = 100,
    interval_minutes: int = 15
) -> List[Dict[str, Any]]:
    """
    Generate bulk test values.

    Args:
        entity_id: Entity ID
        org_id: Organization ID
        count: Number of values to generate
        interval_minutes: Time interval between values

    Returns:
        List of value payloads
    """
    now = datetime.now()
    return [
        {
            "entity_id": entity_id,
            "timestamp": (now - timedelta(minutes=i * interval_minutes)).isoformat(),
            "value": fake.random.uniform(60.0, 80.0)
        }
        for i in range(count)
    ]


def assert_valid_entity_response(response_data: Dict[str, Any]) -> None:
    """
    Validate entity response structure.

    Args:
        response_data: Response data to validate

    Raises:
        AssertionError: If response is invalid
    """
    assert "id" in response_data, "Entity response missing 'id'"
    assert "tags" in response_data, "Entity response missing 'tags'"
    assert isinstance(response_data["tags"], list), "Entity tags should be a list"


def assert_valid_tag_def_response(response_data: Dict[str, Any]) -> None:
    """
    Validate tag definition response structure.

    Args:
        response_data: Response data to validate

    Raises:
        AssertionError: If response is invalid
    """
    assert "id" in response_data, "TagDef response missing 'id'"
    assert "name" in response_data, "TagDef response missing 'name'"


def assert_valid_value_response(response_data: Dict[str, Any]) -> None:
    """
    Validate value response structure.

    Args:
        response_data: Response data to validate

    Raises:
        AssertionError: If response is invalid
    """
    assert "entity_id" in response_data, "Value response missing 'entity_id'"
    assert "timestamp" in response_data, "Value response missing 'timestamp'"
    assert "value" in response_data, "Value response missing 'value'"


def assert_error_response(response_data: Dict[str, Any], expected_status: int = None) -> None:
    """
    Validate error response structure.

    Args:
        response_data: Response data to validate
        expected_status: Expected status code

    Raises:
        AssertionError: If error response is invalid
    """
    assert "detail" in response_data, "Error response missing 'detail'"

    if expected_status:
        # This would need to be checked at the response level
        pass


def generate_random_org_key() -> str:
    """
    Generate random organization key.

    Returns:
        Random org key
    """
    return f"org_{fake.word()}_{fake.random_int(1000, 9999)}"


def generate_random_email() -> str:
    """
    Generate random email address.

    Returns:
        Random email
    """
    return fake.email()


def generate_random_name() -> str:
    """
    Generate random full name.

    Returns:
        Random name
    """
    return fake.name()

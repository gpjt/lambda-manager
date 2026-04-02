from lambda_manager.instance_types import (
    available_instance_type_names,
    instance_type_description_rows,
)
from lambda_manager.lambda_api import (
    DEFAULT_BASE_URL,
    available_region_names,
    build_instance_types_request,
    build_launch_request,
    first_available_region_name,
)
from lambda_manager.telegram import build_send_message_request
from lambda_manager.cli import (
    format_available_instance_types_status,
    format_instance_type_description_table,
)


def test_returns_only_instance_types_with_capacity_available():
    payload = {
        "data": {
            "gpu_1x_h100_sxm5": {
                "regions_with_capacity_available": [{"name": "us-west-1"}]
            },
            "gpu_1x_a10": {"regions_with_capacity_available": []},
            "gpu_2x_a6000": {
                "regions_with_capacity_available": [{"name": "us-east-1"}]
            },
        }
    }

    assert available_instance_type_names(payload) == [
        "gpu_1x_h100_sxm5",
        "gpu_2x_a6000",
    ]


def test_uses_current_lambda_cloud_api_base_url():
    assert DEFAULT_BASE_URL == "https://cloud.lambda.ai/api/v1"


def test_builds_request_with_basic_auth_and_user_agent():
    request = build_instance_types_request(
        "test-api-key", "https://cloud.lambda.ai/api/v1"
    ).prepare()

    assert request.url == "https://cloud.lambda.ai/api/v1/instance-types"
    assert request.headers["Authorization"] == "Basic dGVzdC1hcGkta2V5Og=="
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"] == "lambda-manager/0.1"


def test_returns_first_available_region_for_requested_instance_type():
    payload = {
        "data": {
            "gpu_8x_a100_80gb_sxm4": {
                "regions_with_capacity_available": [
                    {"name": "us-east-1"},
                    {"name": "us-west-1"},
                ]
            }
        }
    }

    assert (
        first_available_region_name(payload, "gpu_8x_a100_80gb_sxm4") == "us-east-1"
    )


def test_returns_all_available_regions_for_requested_instance_type():
    payload = {
        "data": {
            "gpu_8x_a100_80gb_sxm4": {
                "regions_with_capacity_available": [
                    {"name": "us-east-1"},
                    {"name": "us-west-1"},
                ]
            }
        }
    }

    assert available_region_names(payload, "gpu_8x_a100_80gb_sxm4") == [
        "us-east-1",
        "us-west-1",
    ]


def test_builds_launch_request():
    request = build_launch_request(
        api_key="test-api-key",
        base_url="https://cloud.lambda.ai/api/v1",
        region_name="us-east-1",
        instance_type_name="gpu_8x_a100_80gb_sxm4",
        ssh_key_name="default-key",
    ).prepare()

    assert request.url == "https://cloud.lambda.ai/api/v1/instance-operations/launch"
    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/json"
    assert request.body == (
        b'{"region_name": "us-east-1", "instance_type_name": "gpu_8x_a100_80gb_sxm4", '
        b'"ssh_key_names": ["default-key"]}'
    )


def test_builds_telegram_send_message_request():
    request = build_send_message_request(
        bot_token="bot-token",
        chat_id="12345",
        text="Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-123",
        base_url="https://api.telegram.org",
    ).prepare()

    assert request.url == "https://api.telegram.org/botbot-token/sendMessage"
    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert (
        request.body
        == "chat_id=12345&text=Launched+gpu_8x_a100_80gb_sxm4+in+us-east-1+as+instance-123"
    )


def test_formats_available_instance_types_status_with_regions():
    payload = {
        "data": {
            "gpu_2x_a6000": {
                "regions_with_capacity_available": [{"name": "us-east-1"}]
            },
            "gpu_1x_h100_sxm5": {
                "regions_with_capacity_available": [{"name": "us-west-1"}]
            },
            "gpu_1x_a10": {"regions_with_capacity_available": []},
        }
    }

    assert format_available_instance_types_status(payload) == (
        "Available instance types: gpu_1x_h100_sxm5 (regions: us-west-1), "
        "gpu_2x_a6000 (regions: us-east-1)"
    )


def test_returns_instance_type_description_rows_sorted_by_description():
    payload = {
        "data": {
            "gpu_2x_a6000": {
                "instance_type": {"description": "2x A6000"}
            },
            "gpu_1x_h100_sxm5": {
                "instance_type": {"description": "H100 SXM5"}
            },
            "gpu_1x_a10": {
                "instance_type": {"description": "A10"}
            },
        }
    }

    assert instance_type_description_rows(payload) == [
        ("2x A6000", "gpu_2x_a6000"),
        ("A10", "gpu_1x_a10"),
        ("H100 SXM5", "gpu_1x_h100_sxm5"),
    ]


def test_formats_instance_type_description_table():
    rows = [
        ("A10", "gpu_1x_a10"),
        ("H100 SXM5", "gpu_1x_h100_sxm5"),
    ]

    assert format_instance_type_description_table(rows) == (
        "description  name\n"
        "A10          gpu_1x_a10\n"
        "H100 SXM5    gpu_1x_h100_sxm5"
    )

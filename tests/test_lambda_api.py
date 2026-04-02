from lambda_manager.lambda_api import (
    DEFAULT_BASE_URL,
    available_region_names,
    build_instance_types_request,
    build_launch_request,
)


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

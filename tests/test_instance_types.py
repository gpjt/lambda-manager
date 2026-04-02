from lambda_manager.instance_types import available_instance_type_names
from lambda_manager.lambda_api import DEFAULT_BASE_URL, build_request


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
    request = build_request("test-api-key", "https://cloud.lambda.ai/api/v1")

    assert request.full_url == "https://cloud.lambda.ai/api/v1/instance-types"
    assert request.get_header("Authorization") == "Basic dGVzdC1hcGkta2V5Og=="
    assert request.get_header("Accept") == "application/json"
    assert request.get_header("User-agent") == "lambda-manager/0.1"

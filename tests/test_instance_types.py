from lambda_manager.instance_types import (
    available_instance_type_names,
    instance_type_description_rows,
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

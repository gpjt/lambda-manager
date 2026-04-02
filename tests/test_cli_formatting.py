from lambda_manager.formatting import (
    format_available_instance_types_status,
    format_instance_type_description_table,
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

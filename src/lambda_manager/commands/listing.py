from lambda_manager.formatting import format_instance_type_description_table
from lambda_manager.instance_types import (
    available_instance_type_names,
    instance_type_description_rows,
)
from lambda_manager.lambda_api import fetch_instance_types


def handle_list_instance_types() -> int:
    payload = fetch_instance_types()
    for instance_type_name in available_instance_type_names(payload):
        print(instance_type_name)
    return 0


def handle_list_instance_type_descriptions() -> int:
    payload = fetch_instance_types()
    print(
        format_instance_type_description_table(
            instance_type_description_rows(payload)
        )
    )
    return 0

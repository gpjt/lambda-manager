def available_instance_type_names(payload: dict) -> list[str]:
    available_names = []
    for instance_type_name, details in payload.get("data", {}).items():
        if details.get("regions_with_capacity_available"):
            available_names.append(instance_type_name)

    return sorted(available_names)

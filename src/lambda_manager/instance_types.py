def available_instance_type_names(payload: dict) -> list[str]:
    available_names = []
    for instance_type_name, details in payload.get("data", {}).items():
        if details.get("regions_with_capacity_available"):
            available_names.append(instance_type_name)

    return sorted(available_names)


def instance_type_description_rows(payload: dict) -> list[tuple[str, str]]:
    rows = []
    for instance_type_name, details in payload.get("data", {}).items():
        description = details.get("instance_type", {}).get("description", "")
        rows.append((description, instance_type_name))

    return sorted(rows, key=lambda row: row[0])

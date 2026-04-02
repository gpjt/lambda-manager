from lambda_manager.commands.launch import extract_instance_id


def test_extract_instance_id_returns_first_id():
    response = {"data": {"instance_ids": ["instance-123"]}}

    assert extract_instance_id(response) == "instance-123"


def test_extract_instance_id_returns_none_for_missing_ids():
    response = {"data": {"instance_ids": []}}

    assert extract_instance_id(response) is None

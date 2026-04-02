import argparse

from lambda_manager.instance_types import available_instance_type_names
from lambda_manager.lambda_api import fetch_instance_types


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lambda_manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "list-instance-types",
        help="List Lambda Labs instance types that currently have launch capacity",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "list-instance-types":
        payload = fetch_instance_types()
        for instance_type_name in available_instance_type_names(payload):
            print(instance_type_name)
        return 0

    return 1

import argparse

from lambda_manager.commands.launch import handle_launch_when_available
from lambda_manager.commands.listing import (
    handle_list_instance_type_descriptions,
    handle_list_instance_types,
)
from lambda_manager.dotenv import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lambda_manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "list-instance-types",
        help="List Lambda Labs instance types that currently have launch capacity",
    )
    subparsers.add_parser(
        "list-instance-type-descriptions",
        help="List instance type descriptions together with their Lambda API names",
    )
    launch_parser = subparsers.add_parser(
        "launch-when-available",
        help="Poll until a requested instance type has capacity, then launch and notify",
    )
    launch_parser.add_argument("instance_type_name")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)

    if args.command == "list-instance-types":
        return handle_list_instance_types()

    if args.command == "list-instance-type-descriptions":
        return handle_list_instance_type_descriptions()

    if args.command == "launch-when-available":
        return handle_launch_when_available(args.instance_type_name)

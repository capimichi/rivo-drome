import click
from injector import inject

from rivo_drome.command.abstract_command import AbstractCommand
from rivo_drome.service.example_service import ExampleService


class ExampleCommand(AbstractCommand):
    """Example command exposed through Click."""

    command_name = "example"

    @inject
    def __init__(self, example_service: ExampleService):
        self.example_service = example_service

    def run(self, title: str | None = None, message: str | None = None, repeat: int = 1):
        example = self.example_service.get_example(title=title, message=message)
        for idx in range(max(1, repeat)):
            prefix = f"[{idx + 1}] " if repeat > 1 else ""
            click.echo(f"{prefix}{example.title}: {example.message}")

    def register_options(self, fn):
        fn = click.option("--title", "-t", help="Override example title.", default=None)(fn)
        fn = click.option("--message", "-m", help="Override example message.", default=None)(fn)
        fn = click.option(
            "--repeat",
            "-r",
            help="Print the payload multiple times.",
            type=int,
            default=1,
            show_default=True,
        )(fn)
        return fn

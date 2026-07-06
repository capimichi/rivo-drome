import click

from rivo_drome.command.example_command import ExampleCommand
from rivo_drome.command.track_download_command import TrackDownloadCommand
from rivo_drome.container.default_container import DefaultContainer


@click.group()
def cli():
    """Command line entrypoint for the boilerplate."""
    pass


# Resolve dependencies via container, similar to API setup
default_container = DefaultContainer.getInstance()

example_command: ExampleCommand = default_container.get(ExampleCommand)
cli.add_command(example_command.to_click_command())

track_download_command: TrackDownloadCommand = default_container.get(TrackDownloadCommand)
cli.add_command(track_download_command.to_click_command())


if __name__ == '__main__':
    cli()


import click
from injector import inject

from rivo_drome.command.abstract_command import AbstractCommand
from rivo_drome.service.search_service import SearchService
from rivo_drome.service.stream_service import StreamService


class TrackDownloadCommand(AbstractCommand):
    """Command to search and download a track by query."""

    command_name = "track:download"

    @inject
    def __init__(self, search_service: SearchService, stream_service: StreamService):
        self.search_service = search_service
        self.stream_service = stream_service

    def run(self, query: str):
        if not query:
            click.echo("Error: Please provide a search query.")
            return

        click.echo(f"Searching for: '{query}'...")

        # SearchService.search returns a SearchResult3 schema which has artist, album, song lists.
        # We need to run this async, but click command is synchronous.
        import asyncio

        loop = asyncio.get_event_loop()
        search_result = loop.run_until_complete(self.search_service.search(query, song_count=1))

        if not search_result.song:
            click.echo("No tracks found for the given query.")
            return

        track_subsonic = search_result.song[0]
        track_id = int(track_subsonic.id)
        click.echo(f"Found track: '{track_subsonic.title}' (ID: {track_id})")

        click.echo("Starting download...")
        result_path = loop.run_until_complete(self.stream_service.stream_or_download(track_id))

        if result_path:
            click.echo(f"Download completed successfully! Saved to: {result_path}")
        else:
            click.echo("Download failed.")

    def register_options(self, fn):
        fn = click.option(
            "--query",
            "-q",
            help="The search query to find the track.",
            required=True,
            type=str,
        )(fn)
        return fn

from abc import ABC, abstractmethod

import click


class AbstractCommand(ABC):
    """Base command wrapping a run() into a Click command."""

    command_name: str = "command"

    def register_options(self, fn):
        """Hook for subclasses to add Click options."""
        return fn

    @abstractmethod
    def run(self, **kwargs):
        """Execute the command logic."""

    def to_click_command(self) -> click.Command:
        """Return the Click command bound to this instance."""

        @click.command(name=self.command_name)
        @self.register_options
        def command(**kwargs):
            self.run(**kwargs)

        return command

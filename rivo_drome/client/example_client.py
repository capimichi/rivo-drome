from injector import inject


class ExampleClient:
    """Minimal client placeholder for the boilerplate."""

    @inject
    def __init__(self):
        pass

    def fetch_message(self) -> str:
        """Return a static message to demonstrate the client layer."""
        return "Hello from ExampleClient"

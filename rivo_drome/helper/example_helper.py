import re


class ExampleHelper:
    """Utility helpers for example components."""

    @staticmethod
    def slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return slug or "example"

class ExamplePrompt:
    """Holds textual prompts for the example domain."""

    DEFAULT = "This is an example prompt."

    @classmethod
    def format_prompt(cls, subject: str) -> str:
        trimmed = subject.strip() or "example"
        return f"{cls.DEFAULT} Subject: {trimmed}."

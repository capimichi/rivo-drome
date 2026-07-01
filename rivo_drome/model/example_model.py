from pydantic import BaseModel, Field


class ExampleModel(BaseModel):
    """Simple payload used as example across the boilerplate."""

    title: str = Field(default="Example")
    message: str = Field(default="Hello from the boilerplate")

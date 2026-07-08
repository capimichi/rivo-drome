from dataclasses import dataclass


@dataclass
class MusicBrainzConfig:
    user_agent: str = "RivoDrome/1.0.0 (contact@example.com)"

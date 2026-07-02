import json
import os


class NavidromeSampleResponseManager:

    def __init__(self, samples_dir: str):
        self.samples_dir = samples_dir
        os.makedirs(self.samples_dir, exist_ok=True)

    def save_sample(self, request_path: str, response_body: bytes) -> None:
        try:
            parsed = json.loads(response_body)
        except (json.JSONDecodeError, ValueError):
            return

        relative = request_path.strip("/")
        if not relative:
            relative = "root"
        file_path = os.path.join(self.samples_dir, f"{relative}.json")
        file_dir = os.path.dirname(file_path)
        os.makedirs(file_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, default=str)

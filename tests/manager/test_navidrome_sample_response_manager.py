import json
import os
import tempfile

import pytest

from rivo_drome.manager.navidrome_sample_response_manager import NavidromeSampleResponseManager


class TestNavidromeSampleResponseManager:

    def test_save_sample_creates_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = NavidromeSampleResponseManager(samples_dir=tmpdir)
            response_body = json.dumps({"key": "value"}).encode("utf-8")
            manager.save_sample("rest/ping.view", response_body)

            file_path = os.path.join(tmpdir, "rest/ping.view.json")
            assert os.path.exists(file_path)
            with open(file_path) as f:
                data = json.load(f)
            assert data == {"key": "value"}

    def test_save_sample_creates_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = NavidromeSampleResponseManager(samples_dir=tmpdir)
            response_body = json.dumps({"nested": "data"}).encode("utf-8")
            manager.save_sample("a/b/c/resource", response_body)

            file_path = os.path.join(tmpdir, "a/b/c/resource.json")
            assert os.path.exists(file_path)

    def test_save_sample_ignores_non_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = NavidromeSampleResponseManager(samples_dir=tmpdir)
            manager.save_sample("rest/ping.view", b"not json")

            file_path = os.path.join(tmpdir, "rest/ping.view.json")
            assert not os.path.exists(file_path)

    def test_save_sample_handles_root_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = NavidromeSampleResponseManager(samples_dir=tmpdir)
            response_body = json.dumps({"root": True}).encode("utf-8")
            manager.save_sample("", response_body)

            file_path = os.path.join(tmpdir, "root.json")
            assert os.path.exists(file_path)

    def test_samples_dir_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            samples_dir = os.path.join(tmpdir, "sub", "samples")
            NavidromeSampleResponseManager(samples_dir=samples_dir)
            assert os.path.exists(samples_dir)

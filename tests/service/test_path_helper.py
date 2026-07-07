import pytest
from rivo_drome.model.track_info import TrackInfo
from rivo_drome.helper.path_helper import build_structured_path, clean_filename

def test_clean_filename():
    assert clean_filename("Queen/Bowie") == "Queen_Bowie"
    assert clean_filename("A Night? At* The: Opera") == "A Night_ At_ The_ Opera"
    assert clean_filename("   Spaces. ") == "Spaces"
    assert clean_filename(None) == ""

def test_build_structured_path():
    track_info = TrackInfo(
        title="Bohemian / Rhapsody",
        artist="Queen?",
        album="A Night at the Opera*",
        track_number=11,
    )
    path = build_structured_path("/tmp/music", track_info, ".mp3")
    assert path == "/tmp/music/Queen_/A Night at the Opera_/11 - Bohemian _ Rhapsody.mp3"

def test_build_structured_path_no_track_number():
    track_info = TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        album=None,
    )
    path = build_structured_path("/tmp/music", track_info, "flac")
    assert path == "/tmp/music/Queen/Unknown Album/Bohemian Rhapsody.flac"

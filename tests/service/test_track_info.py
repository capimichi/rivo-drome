from rivo_drome.model.track_info import TrackInfo

def test_track_info_has_deezer_id():
    ti = TrackInfo(title="Test", artist="Artist", deezer_id=12345)
    assert ti.deezer_id == 12345

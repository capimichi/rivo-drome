import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from rivo_drome.entity.base import BaseEntity
from rivo_drome.entity.track import Track
from rivo_drome.entity.album import Album
from rivo_drome.entity.artist import Artist

def test_track_album_many_to_many_relationship():
    engine = create_engine("sqlite:///:memory:")
    BaseEntity.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    artist = Artist(name="Queen", deezer_id=123)
    session.add(artist)
    session.commit()
    
    album1 = Album(title="A Night at the Opera", artist_id=artist.id, deezer_id=456)
    album2 = Album(title="Greatest Hits", artist_id=artist.id, deezer_id=789)
    session.add(album1)
    session.add(album2)
    session.commit()
    
    track = Track(
        title="Bohemian Rhapsody",
        artist_id=artist.id,
        track_number=11,
        deezer_id=999,
        status="pending",
    )
    track.albums.append(album1)
    track.albums.append(album2)
    session.add(track)
    session.commit()
    
    session.refresh(track)
    assert len(track.albums) == 2
    assert album1 in track.albums
    assert album2 in track.albums
    
    session.refresh(album1)
    assert len(album1.tracks) == 1
    assert album1.tracks[0] == track
    
    session.close()

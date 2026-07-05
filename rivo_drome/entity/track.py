from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from rivo_drome.entity.base import BaseEntity


class Track(BaseEntity):
    __tablename__ = "track"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artist.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("album.id"), nullable=True)
    duration = Column(Integer, nullable=True)
    track_number = Column(Integer, nullable=True)
    deezer_id = Column(Integer, unique=True, nullable=True)
    local_path = Column(String(1024), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")

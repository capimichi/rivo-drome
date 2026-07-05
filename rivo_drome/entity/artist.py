from datetime import datetime

from sqlalchemy import BigInteger, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from rivo_drome.entity.base import BaseEntity


class Artist(BaseEntity):
    __tablename__ = "artist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    picture_url = Column(String(512), nullable=True)
    deezer_id = Column(BigInteger, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    albums = relationship("Album", back_populates="artist", cascade="all, delete-orphan")
    tracks = relationship("Track", back_populates="artist", cascade="all, delete-orphan")

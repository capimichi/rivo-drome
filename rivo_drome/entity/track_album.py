from sqlalchemy import Table, Column, Integer, ForeignKey
from rivo_drome.entity.base import BaseEntity

track_album = Table(
    "track_album",
    BaseEntity.metadata,
    Column("track_id", Integer, ForeignKey("track.id", ondelete="CASCADE"), primary_key=True),
    Column("album_id", Integer, ForeignKey("album.id", ondelete="CASCADE"), primary_key=True),
)

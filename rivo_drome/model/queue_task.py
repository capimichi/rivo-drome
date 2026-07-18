from pydantic import BaseModel
from typing import Optional

class BaseQueueTask(BaseModel):
    task_id: str

class DownloadTaskPayload(BaseQueueTask):
    song_id: int
    artist_name: str
    title: str

class ConversionTaskPayload(BaseQueueTask):
    song_id: int
    source_format: str
    target_format: str

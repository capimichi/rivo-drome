import pytest
from unittest.mock import MagicMock
from rivo_drome.manager.queue_manager import QueueManager
from rivo_drome.model.queue_task import DownloadTaskPayload

def test_enqueue_task_new():
    mock_redis = MagicMock()
    mock_redis.get_client().zscore.return_value = None
    mock_redis.get_client().pipeline.return_value = MagicMock()
    
    logger = MagicMock()
    manager = QueueManager(mock_redis, logger)
    
    task = DownloadTaskPayload(task_id="t1", song_id=1, artist_name="A", title="T")
    result = manager.enqueue_task("test", task)
    
    assert result is True
    mock_redis.get_client().pipeline.return_value.execute.assert_called_once()

def test_enqueue_task_existing():
    mock_redis = MagicMock()
    mock_redis.get_client().zscore.return_value = 123456789.0
    
    logger = MagicMock()
    manager = QueueManager(mock_redis, logger)
    
    task = DownloadTaskPayload(task_id="t1", song_id=1, artist_name="A", title="T")
    result = manager.enqueue_task("test", task)
    
    assert result is False
    mock_redis.get_client().pipeline.return_value.execute.assert_not_called()

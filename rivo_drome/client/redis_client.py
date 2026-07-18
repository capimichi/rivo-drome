import redis
from injector import inject

class RedisClient:
    @inject
    def __init__(self, host: str = "redis", port: int = 6379, password: str = ""):
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)

    def get_client(self) -> redis.Redis:
        return self.client

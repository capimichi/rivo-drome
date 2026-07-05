from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class DbManager:
    def __init__(self, db_url: str, pool_size: int = 5, max_overflow: int = 10):
        self._engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
        )
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self):
        return self._engine

    def create_session(self) -> Session:
        return self._session_factory()

    def close(self):
        self._engine.dispose()

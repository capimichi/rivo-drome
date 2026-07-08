from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.entity.base import BaseEntity
from rivo_drome.entity.artist import Artist  # noqa: F401
from rivo_drome.entity.album import Album  # noqa: F401
from rivo_drome.entity.track import Track  # noqa: F401
from rivo_drome.entity.track_album import track_album  # noqa: F401


config = context.config

container = DefaultContainer.getInstance()
db_url = container.get_var("db_url")
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseEntity.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

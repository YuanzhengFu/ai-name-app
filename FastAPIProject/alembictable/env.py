import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from models import Base
import settings
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

database_url = settings.DB_URI
if database_url is None:
    raise ValueError("DB_URI没有设置!")
config.set_main_option("sqlalchemy.url", database_url)


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _ensure_alembic_version_capacity(connection: Connection) -> None:
    inspector = sa.inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        return
    version_column = next(
        (column for column in inspector.get_columns("alembic_version") if column["name"] == "version_num"),
        None,
    )
    if not version_column:
        return
    column_type = version_column["type"]
    if getattr(column_type, "length", 0) and column_type.length < 255:
        connection.execute(sa.text("ALTER TABLE alembic_version MODIFY version_num VARCHAR(255) NOT NULL"))


def do_run_migrations(connection: Connection) -> None:
    _ensure_alembic_version_capacity(connection)
    connection.commit()
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

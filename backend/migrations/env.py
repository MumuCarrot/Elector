from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy.pool import NullPool

from alembic import context

from app.core.settings import settings
from app.db.database import Base

# Import all models so they are registered with Base.metadata
from app.models import user, user_profile, user_role, user_role_link
from app.models import election, election_setting, election_access, election_results_cache
from app.models import candidates, attachment

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use sync driver for alembic (psycopg2 instead of asyncpg)
database_url = settings.database_settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section, {}) or {}
    configuration["sqlalchemy.url"] = database_url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

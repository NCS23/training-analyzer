import logging

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Convert sync URL to async if needed
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
elif database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Create tables and ensure schema is up to date."""
    from app.infrastructure.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_columns_exist)


def _ensure_columns_exist(conn):
    """Add missing columns to existing tables (lightweight auto-migration)."""
    from app.infrastructure.database.models import Base

    inspector = sa_inspect(conn)
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for col in table.columns:
            if col.name not in existing_cols:
                col_type = col.type.compile(conn.engine.dialect)

                # Include DEFAULT clause from server_default so NOT NULL
                # columns can be added to tables that already have rows.
                default_clause = ""
                if col.server_default is not None and hasattr(col.server_default, "arg"):
                    default_text = getattr(col.server_default.arg, "text", col.server_default.arg)  # type: ignore[union-attr]
                    raw = str(default_text)
                    # Quote string defaults for PostgreSQL (booleans/numbers are fine unquoted)
                    if raw and not raw.replace(".", "").lstrip("-").isdigit() and raw.lower() not in (
                        "true",
                        "false",
                    ):
                        raw = f"'{raw}'"
                    default_clause = f" DEFAULT {raw}"

                nullable = "NULL" if col.nullable else "NOT NULL"
                sql = (
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" '
                    f"{col_type}{default_clause} {nullable}"
                )
                logger.info(f"Adding missing column: {table_name}.{col.name}")
                conn.execute(text(sql))

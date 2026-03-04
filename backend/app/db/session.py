from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


settings = get_settings()


def _normalize_database_url(url: str) -> str:
    normalized = url
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(normalized)
    if not parsed.query:
        return normalized

    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    rewritten: list[tuple[str, str]] = []
    unsupported_keys = {"channel_binding"}
    for key, value in query_items:
        if key in unsupported_keys:
            continue
        if key == "sslmode":
            rewritten.append(("ssl", value))
        else:
            rewritten.append((key, value))

    return urlunparse(parsed._replace(query=urlencode(rewritten)))


engine = create_async_engine(_normalize_database_url(settings.database_url), echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

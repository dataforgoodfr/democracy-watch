from collections.abc import AsyncGenerator
from typing import Annotated

from asyncpg import (
    CannotConnectNowError,
    InvalidAuthorizationSpecificationError,
    InvalidCatalogNameError,
    PostgresConnectionError,
)
from fastapi import Depends, HTTPException, Request
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    factory = request.app.state.session_factory
    if factory is None:
        raise HTTPException(503, "Base de données non configurée")
    try:
        async with factory() as session:
            yield session
    except (
        OperationalError,
        InterfaceError,
        PoolTimeoutError,
        OSError,
        TimeoutError,
        PostgresConnectionError,
        InvalidAuthorizationSpecificationError,
        InvalidCatalogNameError,
        CannotConnectNowError,
    ):
        raise HTTPException(503, "Base de données temporairement indisponible") from None


DbSession = Annotated[AsyncSession, Depends(get_db)]

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from collections.abc import Generator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)  # noqa: SIM115
tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_db.name}"
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")

import pytest
from fastapi.testclient import TestClient

from backend.app.database import close_db, init_db
from backend.app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
async def _init_db() -> None:
    await init_db()


def _cleanup() -> None:
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_db())
    except BaseException:  # noqa: BLE001, S110
        pass
    try:
        os.unlink(tmp_db.name)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _cleanup_db() -> Generator[None, None, None]:
    yield
    _cleanup()

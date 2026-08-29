import os
import sys
import pytest
import pytest_asyncio

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import init_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    await init_db()
    yield

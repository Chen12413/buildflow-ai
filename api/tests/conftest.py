import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_MODEL"] = "mock-buildflow-v1"
os.environ["LLM_API_MODE"] = "auto"
for variable_name in (
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_CHAT_BASE_URL",
    "DASHSCOPE_RESPONSES_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
):
    os.environ.pop(variable_name, None)

import app.db.session as db_session
import app.services.demo_service as demo_service
import app.services.planning_service as planning_service
import app.services.prd_service as prd_service
import app.services.task_breakdown_service as task_breakdown_service
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

get_settings.cache_clear()


@pytest.fixture()
def client(tmp_path: Path):
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    db_session.engine = engine
    db_session.SessionLocal = testing_session_local
    demo_service.SessionLocal = testing_session_local
    prd_service.SessionLocal = testing_session_local
    planning_service.SessionLocal = testing_session_local
    task_breakdown_service.SessionLocal = testing_session_local
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

import os

os.environ.setdefault("RABBITMQ_URL", "memory://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("DETECTION_TIMEOUT_MS", "300")
os.environ.setdefault("RETRY_BACKOFF_BASE_MS", "1")
os.environ.setdefault("RETRY_BUDGET_MS", "2000")

import fakeredis  # noqa: E402
import pytest  # noqa: E402

import extensiones  # noqa: E402

extensiones.celery_app.conf.task_always_eager = True
extensiones.celery_app.conf.task_eager_propagates = True


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(extensiones, "redis_client", fake)
    return fake

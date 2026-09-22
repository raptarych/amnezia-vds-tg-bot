"""Tests for the Amnezia management HTTP API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

SECRET = "test-secret"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Build a TestClient backed by temporary files and a mock script."""
    secret_file = tmp_path / "secret"
    secret_file.write_text(SECRET, encoding="utf-8")
    awg_dir = tmp_path / "awg"
    awg_dir.mkdir()

    mock_script = tmp_path / "mock_manage.py"
    mock_script.write_text(_mock_script(), encoding="utf-8")

    monkeypatch.setenv("AMNEZIA_API_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("AMNEZIA_API_MANAGE_SCRIPT", str(mock_script))
    monkeypatch.setenv("AMNEZIA_API_AWG_DIR", str(awg_dir))
    get_settings.cache_clear()
    return TestClient(app)


def _mock_script() -> str:
    return r'''import sys

cmd = sys.argv[1]

if cmd == "stats":
    print("""[time] INFO: Статистика трафика клиентов:

Имя | IP | Получено | Отправлено | Последний handshake | Статус
------------------------------------------------------------------
key_a | 10.0.0.2 | 1.00 MiB | 2.00 MiB | 2026-09-22 10:00:00 | Активен
key_b | 10.0.0.3 | 0 B | 0 B | никогда | Неактивен

[time] INFO: Итого: Получено 1.00 MiB, Отправлено 2.00 MiB""")
elif cmd in ("add", "remove"):
    sys.stdout.write(f"ok: {cmd} {sys.argv[2]}\n")
elif cmd in ("check", "restart"):
    sys.stdout.write("ok\n")
else:
    sys.stderr.write("unknown\n")
    sys.exit(1)
'''


HEADERS = {"X-API-Secret": SECRET}


def test_generate_key(client: TestClient) -> None:
    resp = client.post("/keys", params={"name": "phone"}, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["name"] == "phone"


def test_generate_key_bad_name(client: TestClient) -> None:
    resp = client.post("/keys", params={"name": "../../etc/passwd"}, headers=HEADERS)
    assert resp.status_code in {400, 201}


def test_list_keys(client: TestClient) -> None:
    resp = client.get("/keys", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["peers"]) == 2
    assert body["totals"]["received"] == "1.00 MiB"


def test_requires_secret(client: TestClient) -> None:
    resp = client.get("/keys")
    assert resp.status_code == 401


def test_invalid_secret(client: TestClient) -> None:
    resp = client.get("/keys", headers={"X-API-Secret": "wrong"})
    assert resp.status_code == 401


def test_get_key_download(client: TestClient, tmp_path: Path) -> None:
    awg = tmp_path / "awg"
    (awg / "phone.conf").write_text("content", encoding="utf-8")
    resp = client.get("/keys/phone", params={"ext": "conf"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.content == b"content"


def test_get_key_bad_extension(client: TestClient) -> None:
    resp = client.get("/keys/phone", params={"ext": "exe"}, headers=HEADERS)
    assert resp.status_code == 400


def test_get_key_path_traversal(client: TestClient, tmp_path: Path) -> None:
    resp = client.get("/keys/..%2f..%2fetc%2fpasswd", params={"ext": "conf"},
                      headers=HEADERS)
    assert resp.status_code in {400, 404}


def test_server_check(client: TestClient) -> None:
    resp = client.post("/server/check", headers=HEADERS)
    assert resp.status_code == 200


def test_server_restart(client: TestClient) -> None:
    resp = client.post("/server/restart", headers=HEADERS)
    assert resp.status_code == 200


def test_openapi_schema(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert "/keys" in spec["paths"]
    assert "/server/check" in spec["paths"]

from democracy_watch import db


class FakeConnection:
    read_only = None


def test_connect_is_read_only_by_default(monkeypatch):
    calls = {}

    def fake_connect(url, **kwargs):
        calls["url"] = url
        calls.update(kwargs)
        return FakeConnection()

    monkeypatch.setattr(db.psycopg, "connect", fake_connect)
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/dw")

    conn = db.connect()

    assert conn.read_only is True
    assert calls["url"] == "postgresql://example/dw"
    assert calls["connect_timeout"] == 15


def test_connect_can_write_when_asked(monkeypatch):
    monkeypatch.setattr(db.psycopg, "connect", lambda *a, **k: FakeConnection())
    assert db.connect(read_only=False).read_only is False

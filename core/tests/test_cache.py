import time, json
from core.memory.db import cache_put, cache_get, init


def test_cache_query_performance(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_DB", str(tmp_path / "cache.sqlite"))
    init()
    for i in range(1000):
        cache_put("t", str(i), json.dumps({"i": i}))
    start = time.time()
    for i in range(1000):
        assert cache_get("t", str(i)) is not None
    elapsed = time.time() - start
    # query by primary key should be fast
    assert elapsed < 1.0


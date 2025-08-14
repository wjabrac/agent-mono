import os
import time
import types
from core.security.policy import enforce_http_rate_limit


def test_http_rate_limit(monkeypatch):
	monkeypatch.setenv("POLICY_ENGINE_ENABLED", "true")
	monkeypatch.setenv("HTTP_RATE_LIMIT_PER_MIN", "1")
	# First call ok
	enforce_http_rate_limit("web_fetch", {"url": "https://example.com"})
	# Second call rate limited
	try:
		enforce_http_rate_limit("web_fetch", {"url": "https://example.com"})
		assert False
	except RuntimeError as e:
		assert "rate_limited" in str(e)
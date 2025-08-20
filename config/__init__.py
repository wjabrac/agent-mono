"""Configuration defaults for the agent runtime.

Environment variables take precedence over these defaults:

```
POLICY_ENGINE_ENABLED  # "1", "true", or "yes" enable the policy engine (default: true)
POLICY_PATH            # Path to the policy file (default: "./policies.json")
```
"""

from __future__ import annotations

import os


def _env_bool(name: str, default: str) -> bool:
    return os.environ.get(name, default).lower() in {"1", "true", "yes"}


POLICY_ENGINE_ENABLED = _env_bool("POLICY_ENGINE_ENABLED", "true")
POLICY_PATH = os.environ.get("POLICY_PATH", "./policies.json")


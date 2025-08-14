from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List


_listeners: Dict[str, List[Callable]] = defaultdict(list)


def on(event: str, func: Callable) -> None:
    _listeners[event].append(func)


def emit(event: str, *args, **kwargs) -> None:
    for func in list(_listeners.get(event, [])):
        func(*args, **kwargs)

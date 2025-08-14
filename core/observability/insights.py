import os
import json
import statistics
from typing import Dict, Any, List, Tuple
from datetime import datetime

from core.observability.metrics import (
    tool_calls_total,
    tool_latency_ms,
    tool_skipped_total,
)
from core.observability.trace import get_trace_summary, get_conn


def _percentiles(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0, "avg": 0.0}
    vals = sorted(values)
    n = len(vals)
    p50 = vals[int(0.5 * (n - 1))]
    p95 = vals[int(0.95 * (n - 1))]
    return {
        "p50": float(p50),
        "p95": float(p95),
        "avg": float(statistics.fmean(vals)),
    }


def _gather_trace_rollups() -> Dict[str, Any]:
    """Aggregate trace_events table for error and skip reasons per tool."""
    c = get_conn()
    rows = c.execute(
        "SELECT role, payload FROM trace_events ORDER BY created_at DESC LIMIT 5000"
    ).fetchall()
    c.close()
    errors: Dict[str, int] = {}
    errors_by_type: Dict[str, int] = {}
    skipped: Dict[Tuple[str, str], int] = {}
    for role, payload in rows:
        try:
            data = json.loads(payload)
        except Exception:
            continue
        if role == "executor:error":
            tool = data.get("tool", "<unknown>")
            etype = data.get("error", "<unknown>")
            errors[tool] = errors.get(tool, 0) + 1
            errors_by_type[etype] = errors_by_type.get(etype, 0) + 1
        elif role == "executor:skip":
            tool = data.get("tool", "<unknown>")
            reason = data.get("reason", "unknown")
            skipped[(tool, reason)] = skipped.get((tool, reason), 0) + 1
    # flatten skipped by reason
    skipped_by_tool: Dict[str, Dict[str, int]] = {}
    for (tool, reason), cnt in skipped.items():
        skipped_by_tool.setdefault(tool, {})[reason] = skipped_by_tool.get(tool, {}).get(reason, 0) + cnt
    return {
        "errors": errors,
        "errors_by_type": errors_by_type,
        "skipped_by_tool": skipped_by_tool,
    }


def _tool_stats() -> Dict[str, Any]:
    """Summarize successes/failures, latencies, and skips from local counters."""
    successes: Dict[str, int] = {}
    failures: Dict[str, int] = {}
    for (tool, ok), cnt in tool_calls_total._data.items():  # type: ignore[attr-defined]
        if ok == "true":
            successes[tool] = successes.get(tool, 0) + cnt
        else:
            failures[tool] = failures.get(tool, 0) + cnt
    lat: Dict[str, Dict[str, float]] = {}
    for (tool,), values in tool_latency_ms._data.items():  # type: ignore[attr-defined]
        lat[tool] = _percentiles(values)
    skipped: Dict[str, Dict[str, int]] = {}
    for (tool, reason), cnt in tool_skipped_total._data.items():  # type: ignore[attr-defined]
        skipped.setdefault(tool, {})[reason] = skipped.get(tool, {}).get(reason, 0) + cnt
    # merge into tool entries
    tools: Dict[str, Any] = {}
    all_names = set(successes) | set(failures) | set(lat) | set(skipped)
    for name in all_names:
        total = successes.get(name, 0) + failures.get(name, 0)
        fail = failures.get(name, 0)
        sr = 0.0 if total == 0 else (successes.get(name, 0) / total)
        tools[name] = {
            "calls": total,
            "successes": successes.get(name, 0),
            "failures": fail,
            "success_rate": round(sr, 4),
            "latency_ms": lat.get(name, {"p50": 0.0, "p95": 0.0, "avg": 0.0}),
            "skipped": skipped.get(name, {}),
        }
    return tools


def _recommendations(tools: Dict[str, Any], trace_rollups: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    # High-value targets: high usage, high fail
    for name, info in sorted(tools.items(), key=lambda x: -x[1]["calls"]):
        calls = info["calls"]
        failures = info["failures"]
        sr = info["success_rate"]
        p95 = info["latency_ms"].get("p95", 0.0)
        skipped_map = info.get("skipped", {})
        if calls >= 5 and sr < 0.85 and failures >= 3:
            recs.append(f"Improve '{name}': failure rate {failures}/{calls} (SR={sr:.2f}). Add retries/timeouts, validate inputs, and unit tests.")
        if calls >= 5 and p95 > 2000:
            recs.append(f"Optimize '{name}': high p95 latency {int(p95)}ms. Consider caching outputs or simplifying work.")
        if skipped_map.get("not_found", 0) >= 3:
            recs.append(f"Define or alias missing tool '{name}': observed {skipped_map['not_found']} not_found events.")
        if skipped_map.get("prior_error", 0) >= 3:
            recs.append(f"Reorder/guard pipeline: '{name}' often skipped due to prior errors ({skipped_map['prior_error']}). Add pre-checks or make upstream steps robust.")
    # Common error classes
    by_type = trace_rollups.get("errors_by_type", {})
    top_errs = sorted(by_type.items(), key=lambda x: -x[1])[:5]
    if top_errs:
        err_desc = ", ".join([f"{k}:{v}" for k, v in top_errs])
        recs.append(f"Top error types: {err_desc}. Prioritize fixes/tests for these.")
    if not recs:
        recs.append("System appears stable. Consider expanding tool coverage or adding DAG/parallel execution for throughput.")
    return recs


def compute_insights(persist_path: str | None = None) -> Dict[str, Any]:
    tools = _tool_stats()
    traces = _gather_trace_rollups()
    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "tools": tools,
        "trace_rollups": traces,
        "recommendations": _recommendations(tools, traces),
    }
    if persist_path:
        try:
            os.makedirs(os.path.dirname(persist_path), exist_ok=True)
            with open(persist_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return out
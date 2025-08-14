from typing import List, Dict, Any
from core.tools.microtool import microtool
from core.tools.manifest import load_manifest


@microtool("tool.select", description="Select best tool for a capability given context tags", tags=["select","routing"])
def tool_select(capability: str, context_tags: List[str] | None = None, candidates: List[str] | None = None) -> dict:
	mf = load_manifest()
	context_tags = context_tags or []
	tools = candidates or list(mf.keys())
	scores: List[Dict[str, Any]] = []
	for name in tools:
		entry = mf.get(name) or {}
		tags = set(entry.get("tags") or [])
		provides = set(entry.get("provides") or [])
		score = 0.0
		if capability in provides or capability in tags:
			score += 3.0
		score += float(len(set(context_tags) & tags))
		score += 0.1 * float(int(entry.get("uses", 0)))
		scores.append({"tool": name, "score": score, "tags": sorted(tags), "provides": sorted(provides)})
	scores.sort(key=lambda x: x["score"], reverse=True)
	return {"chosen": scores[0]["tool"] if scores else None, "ranking": scores}
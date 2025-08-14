import os, json, time, logging
from typing import Dict, Any, List
from pydantic import ValidationError

MANIFEST_PATH = os.getenv("TOOLS_MANIFEST_PATH", "data/tools_manifest.json")


def _ensure_manifest_exists() -> None:
	root = os.path.dirname(MANIFEST_PATH) or "."
	os.makedirs(root, exist_ok=True)
	if not os.path.exists(MANIFEST_PATH):
		with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
			json.dump({}, f)


def load_manifest() -> Dict[str, Any]:
        _ensure_manifest_exists()
        try:
                with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                        return json.load(f) or {}
        except (IOError, ValidationError) as e:
                logging.getLogger(__name__).error("failed to load manifest: %s", e)
                return {}


def save_manifest(mf: Dict[str, Any]) -> None:
	_ensure_manifest_exists()
	with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
		json.dump(mf, f, ensure_ascii=False, indent=2)


def ensure_tool_entry(name: str, path: str = "", tags: List[str] | None = None, composite_of: List[str] | None = None, description: str = "") -> None:
	mf = load_manifest()
	if name not in mf:
		mf[name] = {"path": path, "uses": 0, "errors": 0, "tags": tags or [], "composite_of": composite_of or [], "description": description, "last_used": 0}
		save_manifest(mf)


def register_usage(name: str, success: bool = True, tags: List[str] | None = None, path: str = "", description: str = "") -> None:
	mf = load_manifest()
	entry = mf.get(name) or {"path": path, "uses": 0, "errors": 0, "tags": [], "composite_of": [], "description": description, "last_used": 0}
	entry["uses"] = int(entry.get("uses", 0)) + 1
	if not success:
		entry["errors"] = int(entry.get("errors", 0)) + 1
	if tags:
		# merge unique tags
		existing = set(entry.get("tags", []))
		entry["tags"] = sorted(existing.union(tags))
	entry["last_used"] = int(time.time())
	entry["path"] = entry.get("path") or path
	entry["description"] = entry.get("description") or description
	mf[name] = entry
	save_manifest(mf)


def get_top_tools(k: int = 10) -> List[Dict[str, Any]]:
	mf = load_manifest()
	items = [{"name": n, **v} for n, v in mf.items()]
	items.sort(key=lambda x: (-int(x.get("uses", 0)), x["name"]))
	return items[:k]
import os, re, json, tempfile, shutil, subprocess
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel
from core.tools.microtool import microtool
from core.tools.registry import discover
from core.tools.manifest import load_manifest, save_manifest


class ImportInput(BaseModel):
	repo: str  # git URL or local path
	goal: str = ""
	allow_network: bool = False
	limit_files: int = 500


def _is_git_url(s: str) -> bool:
	return s.startswith("http://") or s.startswith("https://") or s.endswith(".git")


def _clone_if_needed(repo: str, allow_network: bool) -> Tuple[str, str]:
	if _is_git_url(repo):
		if not allow_network:
			raise RuntimeError("network_disabled_for_clone")
		tmp = tempfile.mkdtemp(prefix="cap_import_")
		dest = os.path.join(tmp, "repo")
		res = subprocess.run(["git", "clone", "--depth", "1", repo, dest], capture_output=True, text=True)
		if res.returncode != 0:
			shutil.rmtree(tmp, ignore_errors=True)
			raise RuntimeError(f"git_clone_failed: {res.stderr.strip()}")
		return dest, tmp
	else:
		if not os.path.isdir(repo):
			raise RuntimeError("repo_path_not_found")
		return os.path.abspath(repo), ""


def _analyze_repo(root: str, limit_files: int) -> Dict[str, Any]:
	flags = {"http": False, "transform": False, "paginate": False, "conditional": False}
	files_scanned = 0
	matches: Dict[str, int] = {k: 0 for k in flags}
	for dirpath, _, filenames in os.walk(root):
		for fn in filenames:
			if not fn.endswith((".ts", ".js", ".py", ".json")):
				continue
			try:
				with open(os.path.join(dirpath, fn), "r", encoding="utf-8", errors="ignore") as f:
					txt = f.read()
			except Exception:
				continue
			files_scanned += 1
			if files_scanned > limit_files:
				break
			if re.search(r"helpers\\.request|requestWithAuthentication|\\baxios\\b|\\bfetch\\b|\\bgot\\b", txt):
				flags["http"] = True; matches["http"] += 1
			if re.search(r"getNodeParameter|parameters\s*:\s*\[", txt):
				flags["transform"] = True; matches["transform"] += 1
			if re.search(r"page(size)?|limit|offset|nextPage|hasMore|cursor", txt, re.IGNORECASE):
				flags["paginate"] = True; matches["paginate"] += 1
			if re.search(r"if\s*\(|continueOnFail|conditional|switch", txt):
				flags["conditional"] = True; matches["conditional"] += 1
	steps: List[Dict[str, Any]] = []
	if flags["http"]:
		steps.append({"primitive": "http_request", "reason": "HTTP patterns detected (axios/fetch/request)"})
	if flags["transform"]:
		steps.append({"primitive": "transform_map", "reason": "Parameter extraction / field mapping patterns detected"})
	if flags["paginate"]:
		steps.append({"primitive": "batch", "reason": "Pagination fields detected", "note": "Implement batch/paginate microtool if needed"})
	if flags["conditional"]:
		steps.append({"primitive": "filter_if", "reason": "Conditional patterns detected", "note": "Implement filter_if microtool if needed"})
	return {"flags": flags, "matches": matches, "files_scanned": files_scanned, "step_specs": steps}


def _ensure_file(path: str, content: str) -> bool:
	if os.path.exists(path):
		return False
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as f:
		f.write(content)
	return True


def _scaffold_primitives(tools_dir: str) -> List[str]:
	created: List[str] = []
	# http_request
	http_path = os.path.join(tools_dir, "http_request.py")
	http_code = (
		"from pydantic import BaseModel\n"
		"from core.tools.microtool import microtool\n\n"
		"try:\n\thttpx = __import__(\"httpx\")\nexcept Exception:\n\thttpx = None\n"
		"try:\n\trequests = __import__(\"requests\")\nexcept Exception:\n\trequests = None\n\n"
		"class HttpInput(BaseModel):\n\turl: str\n\tmethod: str = \"GET\"\n\theaders: dict | None = None\n\tparams: dict | None = None\n\tjson: dict | None = None\n\tdata: dict | None = None\n\ttimeout_s: int = 20\n\tparse_json: bool = True\n\n"
		"@microtool(\"http_request\", description=\"Generic HTTP request primitive (GET/POST/etc)\", tags=[\"http\",\"network\",\"request\"], input_model=HttpInput)\n"
		"def http_request(url, method=\"GET\", headers=None, params=None, json=None, data=None, timeout_s=20, parse_json=True) -> dict:\n"
		"\tif httpx is not None:\n\t\twith httpx.Client(timeout=timeout_s) as c:\n\t\t\tr = c.request(method, url, headers=headers, params=params, json=json, data=data)\n\t\t\tr.raise_for_status()\n\t\t\treturn {\"status\": r.status_code, \"headers\": dict(r.headers), \"json\": r.json()} if parse_json else {\"status\": r.status_code, \"headers\": dict(r.headers), \"text\": r.text}\n"
		"\telif requests is not None:\n\t\tr = requests.request(method, url, headers=headers, params=params, json=json, data=data, timeout=timeout_s)\n\t\tr.raise_for_status()\n\t\treturn {\"status\": r.status_code, \"headers\": dict(r.headers), \"json\": r.json()} if parse_json else {\"status\": r.status_code, \"headers\": dict(r.headers), \"text\": r.text}\n\telse:\n\t\traise RuntimeError(\"no_http_client_available\")\n"
	)
	if _ensure_file(http_path, http_code):
		created.append("http_request")
	# transform_map
	trans_path = os.path.join(tools_dir, "transform_map.py")
	trans_code = (
		"from pydantic import BaseModel\n"
		"from core.tools.microtool import microtool\n\n"
		"class TransformInput(BaseModel):\n\titems: list[dict]\n\tmapping: dict\n\n"
		"@microtool(\"transform_map\", description=\"Map/rename fields using dot-paths or literals\", tags=[\"transform\",\"map\"], input_model=TransformInput)\n"
		"def transform_map(items, mapping) -> dict:\n\tdef get_path(d: dict, p: str):\n\t\tcur = d\n\t\tfor k in p.split(\".\"):\n\t\t\tcur = cur.get(k) if isinstance(cur, dict) else None\n\t\treturn cur\n\tout = []\n\tfor it in items:\n\t\trow = {}\n\t\tfor out_key, spec in mapping.items():\n\t\t\tif isinstance(spec, str):\n\t\t\t\trow[out_key] = get_path(it, spec) if \".\" in spec else it.get(spec)\n\t\t\telse:\n\t\t\t\trow[out_key] = spec\n\t\tout.append(row)\n\treturn {\"items\": out}\n"
	)
	if _ensure_file(trans_path, trans_code):
		created.append("transform_map")
	return created


@microtool("capability.import", description="Fetch a repo, infer mid-steps, scaffold primitives, and register", tags=["capability","import","dissolve"], input_model=ImportInput)
def capability_import(repo: str, goal: str = "", allow_network: bool = False, limit_files: int = 500) -> dict:
	root, tmp_root = _clone_if_needed(repo, allow_network)
	try:
		analysis = _analyze_repo(root, limit_files)
		# Scaffold core primitives if missing
		created = _scaffold_primitives(os.path.join(os.getcwd(), "tools"))
		# Update manifest metadata
		mf = load_manifest()
		for name in created:
			entry = mf.get(name) or {}
			tags = set(entry.get("tags") or [])
			provides = set(entry.get("provides") or [])
			if name == "http_request":
				provides.update({"http_request","fetch","api_call"}); tags.update({"http","network"})
			elif name == "transform_map":
				provides.update({"transform","map","reshape"}); tags.update({"transform","map"})
			entry["tags"] = sorted(tags)
			entry["provides"] = sorted(provides)
			entry["source_repo"] = repo
			mf[name] = entry
		save_manifest(mf)
		# Reload discovery so newly created microtools register
		discover("")
		return {"flags": analysis["flags"], "step_specs": analysis["step_specs"], "files_scanned": analysis["files_scanned"], "created_tools": created, "notes": "Scaffolded primitives if missing; consider adding batch/filter_if primitives as needed."}
	finally:
		if tmp_root:
			shutil.rmtree(tmp_root, ignore_errors=True)
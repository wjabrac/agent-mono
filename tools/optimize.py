from core.tools.microtool import microtool
from tools.search import search
from tools.compare import compare

@microtool("optimize", description="Simple composite: search then compare first match", tags=["composite"])
def optimize(data: list[str], term: str, cmp: str) -> dict:
	res = search(data=data, term=term)
	first = res["matches"][0] if res["count"] else None
	cmp_res = compare(first, cmp)
	return {"search": res, "compare": cmp_res}
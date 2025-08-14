from core.tools.microtool import microtool
from core.tools.registry import get

@microtool("optimize", description="Simple composite: search then compare first match", tags=["composite"])
def optimize(data: list[str], term: str, cmp: str) -> dict:
    search_spec = get("search")
    compare_spec = get("compare")
    res = search_spec.run({"data": data, "term": term})
    first = res["matches"][0] if res["count"] else None
    cmp_res = compare_spec.run({"a": first, "b": cmp})
    return {"search": res, "compare": cmp_res}

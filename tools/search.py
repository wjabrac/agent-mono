from core.tools.microtool import microtool

@microtool("search", description="Search for a term in a list", tags=["search","list"])
def search(data: list[str], term: str, case_sensitive: bool = False) -> dict:
	if case_sensitive:
		matches = [x for x in data if term in str(x)]
	else:
		matches = [x for x in data if term.lower() in str(x).lower()]
	return {"matches": matches, "count": len(matches)}
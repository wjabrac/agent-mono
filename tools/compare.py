from core.tools.microtool import microtool

@microtool("compare", description="Compare two values", tags=["compare"])
def compare(a, b) -> dict:
	return {"equal": a == b, "a": a, "b": b}
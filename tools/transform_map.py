from pydantic import BaseModel
from core.tools.microtool import microtool


class TransformInput(BaseModel):
	items: list[dict]
	mapping: dict  # {"out_field": "in.path" or literal}


@microtool("transform_map", description="Map/rename fields using dot-paths or literals", tags=["transform","map"], input_model=TransformInput)
def transform_map(items, mapping) -> dict:
	def get_path(d: dict, p: str):
		cur = d
		for k in p.split("."):
			cur = cur.get(k) if isinstance(cur, dict) else None
		return cur
	out = []
	for it in items:
		row = {}
		for out_key, spec in mapping.items():
			if isinstance(spec, str):
				row[out_key] = get_path(it, spec) if "." in spec else it.get(spec)
			else:
				row[out_key] = spec
		out.append(row)
	return {"items": out}
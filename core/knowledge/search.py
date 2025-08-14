import os, json
from typing import Any, List, Dict

ENABLE_SEMANTIC_SEARCH = os.getenv("ENABLE_SEMANTIC_SEARCH", "false").lower() in ("1","true","yes")
VENDOR = os.getenv("SEMANTIC_VENDOR", "qdrant")

try:
	from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
	SentenceTransformer = None  # type: ignore

# Optional Qdrant
try:
	from qdrant_client import QdrantClient  # type: ignore
	from qdrant_client.http.models import Distance, VectorParams, PointStruct  # type: ignore
except Exception:
	QdrantClient = None  # type: ignore
	Distance = VectorParams = PointStruct = None  # type: ignore

# Optional Meilisearch
try:
	import meilisearch  # type: ignore
except Exception:
	meilisearch = None  # type: ignore

_model = None
_client = None
_collection = os.getenv("SEMANTIC_COLLECTION", "agent_events")


def _ensure_model():
	global _model
	if _model is None and ENABLE_SEMANTIC_SEARCH and SentenceTransformer:
		_model = SentenceTransformer(os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
	return _model


def _ensure_client():
	global _client
	if _client is not None:
		return _client
	if not ENABLE_SEMANTIC_SEARCH:
		return None
	if VENDOR == "qdrant" and QdrantClient:
		_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
		try:
			_client.recreate_collection(
				collection_name=_collection,
				vectors_config=VectorParams(size=384, distance=Distance.COSINE),
			)
		except Exception:
			pass
	elif VENDOR == "meilisearch" and meilisearch:
		_client = meilisearch.Client(os.getenv("MEILI_URL", "http://localhost:7700"), os.getenv("MEILI_KEY", ""))
		try:
			_client.get_or_create_index(_collection)
		except Exception:
			pass
	return _client


def maybe_index_event(event_id: str, trace_id: str, phase: str, role: str, payload: Any) -> None:
	if not ENABLE_SEMANTIC_SEARCH:
		return
	model = _ensure_model(); client = _ensure_client()
	if model is None or client is None:
		return
	text = json.dumps({"phase": phase, "role": role, "payload": payload}, ensure_ascii=False)
	vec = model.encode([text])[0].tolist() if hasattr(model, "encode") else None
	if vec is None:
		return
	if VENDOR == "qdrant" and isinstance(client, object) and QdrantClient:
		try:
			client.upsert(collection_name=_collection, points=[PointStruct(id=event_id, vector=vec, payload={"trace_id": trace_id, "text": text})])
		except Exception:
			return
	elif VENDOR == "meilisearch" and meilisearch:
		try:
			client.index(_collection).add_documents([{ "id": event_id, "trace_id": trace_id, "text": text, "vector": vec }])
		except Exception:
			return


def semantic_query(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
	"""Search previously indexed events/documents.

	Returns a list of {"trace_id", "text", "score"}.
	If semantic search is disabled or clients are unavailable, return [].
	"""
	if not ENABLE_SEMANTIC_SEARCH:
		return []
	model = _ensure_model(); client = _ensure_client()
	if model is None or client is None:
		return []
	if VENDOR == "qdrant" and QdrantClient and hasattr(client, "search"):
		vec = model.encode([query])[0].tolist()
		try:
			res = client.search(collection_name=_collection, query_vector=vec, limit=top_k)
			rets = []
			for r in res:
				rets.append({"trace_id": r.payload.get("trace_id"), "text": r.payload.get("text"), "score": float(getattr(r, "score", 0.0))})
			return rets
		except Exception:
			return []
	elif VENDOR == "meilisearch" and meilisearch:
		try:
			res = client.index(_collection).search(query, {"limit": top_k})
			hits = res.get("hits", []) if isinstance(res, dict) else getattr(res, "hits", [])
			return [{"trace_id": h.get("trace_id"), "text": h.get("text"), "score": 0.0} for h in hits]
		except Exception:
			return []
	return []
import importlib, os, tempfile


def setup_module(module):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    os.environ["AGENT_DB"] = path
    import core.memory.db as db
    importlib.reload(db)
    db.init()
    module.db = db
    os.environ["ENABLE_SEMANTIC_SEARCH"] = "false"
    import core.knowledge.search as ks
    importlib.reload(ks)
    module.ks = ks


def teardown_module(module):
    db_path = os.environ.get("AGENT_DB")
    if db_path and os.path.exists(db_path):
        os.remove(db_path)
    if "AGENT_DB" in os.environ:
        del os.environ["AGENT_DB"]
    import importlib
    import core.memory.db as db_module
    importlib.reload(db_module)
    db_module.init()


def test_message_roundtrip():
    import core.tools.mcp_adapter as mcp
    importlib.reload(mcp)
    mcp._agent_message({
        "thread_id": "t1",
        "sender": "alice",
        "recipient": "bob",
        "content": "hello bob",
    })
    inbox = mcp._agent_inbox({"thread_id": "t1", "recipient": "bob"})
    assert any(m["content"] == "hello bob" for m in inbox["messages"])


def test_keyword_and_hybrid_search():
    with db.get_conn() as c:
        c.execute("INSERT OR REPLACE INTO traces(id, thread_id) VALUES(?,?)", ("tr1", "t1"))
        c.execute(
            "INSERT INTO trace_events(id, trace_id, phase, role, payload) VALUES(?,?,?,?,?)",
            ("ev1", "tr1", "phase", "role", "This is a hello message"),
        )
    res_kw = ks.keyword_query("hello")
    assert any("hello" in r["text"].lower() for r in res_kw)
    res_hyb = ks.hybrid_query("hello")
    assert res_hyb

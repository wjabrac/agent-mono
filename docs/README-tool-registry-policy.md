### Tool registry
- Tools implement `core.tools.registry.ToolSpec` and are auto-discovered in `plugins/`.
- Enable hot reload and remote tool configs:
```bash
export TOOL_HOT_RELOAD=true
export REMOTE_TOOLS_CONFIG=/path/to/tools.json
```
`tools.json` example:
```json
{
  "tools": [
    {"name": "weather", "url": "https://api.example.com/weather", "api_key_env": "WEATHER_KEY", "result_path": "data"}
  ]
}
```

### Policy engine
Enable and configure:
```bash
export POLICY_ENGINE_ENABLED=true
export ALLOWED_TOOLS=web_fetch,pdf_text,csv_parse,json_parse,image_info
export FS_SAFE_ROOTS=$PWD
export HTTP_RATE_LIMIT_PER_MIN=30
```

### Human-in-the-loop (HITL)
- Approvals are required for multi-step waves by default. Disable with:
```bash
export HITL_DEFAULT=false
```
- Per-step approvals:
```bash
export HITL_PER_STEP=true
```
- Approve by creating a `hitl.ok` file (path controlled by `HITL_TOKEN`).

### Advanced planning and reflection
```bash
export ADVANCED_PLANNING=true
export ENABLE_REFLECTION=true
```
Plans can include conditionals and loops; the engine expands them before execution.
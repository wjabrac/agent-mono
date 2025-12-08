# Quick start

This guide shows how to try the experimental agent runtime. For an overview of the architecture and features, see the [README](../README.md).

The agent now maintains a persistent vector memory backed by ChromaDB so context is reused across sessions.

## Installation

```bash
pip install --no-deps -e .
```

Include extras to enable plugin dependencies:

```bash
pip install --no-deps -e .[http,images]
```

The `[http]` extra installs `httpx` for network tools and `[images]` installs
`Pillow` for image utilities.

Install OpenTelemetry libraries to capture metrics and traces:
```bash
pip install opentelemetry-api opentelemetry-sdk
```
Set `OTEL_SDK_DISABLED=false` to enable exporting spans; otherwise only the
local trace store is used.

Any Python package manager can be used. The project targets Python 3.10+.

## Running an instruction

```bash
agent "list files in /tmp"
```
Running the command prints diagnostics to stderr and one JSON object to stdout:

```
policy mode=loaded path=policies.json schema=1
discovered 7 tools in 3 ms: csv_parse, json_parse, ...
{"instruction": "list files in /tmp", "tools": ["csv_parse"], "version": 1, "trace_id": "...", "result": {"outputs": [...]}}
```
There is no other stdout text.

## Creating a plugin

```bash
agent create plugin my_plugin
```

A new folder `plugins/my_plugin` is created with a minimal `ToolSpec` that you
can extend. To scaffold a service instead:

```bash
agent create service my_service
```

Plugins execute in a sandboxed subprocess with strict CPU and memory limits.
Validate all inputs and outputs with Pydantic models as shown in the templates.
See [plugin-security](plugin-security.md) for more details.

## Enabling optional modules

Advanced modules provide planning, security, and observability. All advanced features are disabled by default. Enable them with environment variables:

```bash
export TOOL_HOT_RELOAD=true              # reload plugins without restart
export POLICY_ENGINE_ENABLED=true        # allowlist, path restrictions, rate limits
export ADVANCED_PLANNING=true            # plan conditionals and loops
export HITL_DEFAULT=true                 # require human approvals
```

The default `policies.json` denies network access, filesystem writes, and
subprocess execution. Adjust the file or declare environment variables like
`ALLOWED_TOOLS` and `FS_SAFE_ROOTS` to permit only the operations you need:

```bash
export ALLOWED_TOOLS=web_fetch
export FS_SAFE_ROOTS=$PWD
```

These variables activate the planning, security, and observability capabilities.
For design details see [`docs/architecture/tool-runtime-and-planning.md`](architecture/tool-runtime-and-planning.md) and the [README](../README.md).

Risky tools run in a sandboxed subprocess on POSIX systems. On non-POSIX
platforms tools are denied unless `ALLOW_UNSAFE_SANDBOX=1` is set, which prints
a warning and executes the tool without isolation.

## Natural language decomposition and reflection

Turn on planning flags to let the runtime break down natural-language goals into
multiple steps and optional checkpoints:

```bash
export ADVANCED_PLANNING=true         # expand loops/conditionals in plans
export ENABLE_REFLECTION=true         # add self-reflection checkpoints
export HITL_DEFAULT=false             # skip human approvals for unattended runs
```

Then run free-form tasks similar to Open Interpreter:

```bash
ADVANCED_PLANNING=true agent "Draft a 3-step plan to summarize ./docs and execute it"
```

The agent will emit a JSON trace containing the decomposed plan steps and
results. Keep policy flags (`POLICY_ENGINE_ENABLED`, `ALLOWED_TOOLS`,
`FS_SAFE_ROOTS`) tuned to the resources you intend to allow during execution.

## Using voice as the front-end

There is a built-in voice loop if you prefer a hands-free workflow. It records
audio, sends it through a configurable STT command, runs the agent, and
optionally speaks the reply:

```bash
VOICE_STT_COMMAND="whisper.cpp -f {file} -otxt --print-colors false" \
VOICE_TTS_COMMAND='tmpfile=$(mktemp /tmp/agent_reply_XXXX.wav); espeak -w "$tmpfile" {text}; play "$tmpfile"; rm -f "$tmpfile"' \
VOICE_RECORD_COMMAND="ffmpeg -hide_banner -loglevel error -f alsa -i default -t 6 -ac 1 -ar 16000 {file}" \
npm run voice
```

- `VOICE_STT_COMMAND` is required and must print the transcription to stdout.
  Use `{file}` to reference the recorded WAV file.
- `VOICE_TTS_COMMAND` is optional and should speak the `{text}` placeholder for
  the agent response; the `{text}` substitution is shell-escaped for safety.
- `VOICE_RECORD_COMMAND` controls microphone capture; override it if your
  environment needs a different `ffmpeg` input target. Set
  `VOICE_RECORD_SECONDS` to adjust duration. Set `VOICE_COMMAND_TIMEOUT_MS` to
  cap how long capture or playback commands can run.
- Tune personality and creativity with `AGENT_PERSONA` and
  `AGENT_RESPONSE_TEMPERATURE`; the default persona is "resilient, creative, and
  highly effective" while staying grounded in facts.

Press Enter to trigger recording or type directly into the prompt. The loop uses
the same planning flags as the CLI, so you can combine `ADVANCED_PLANNING` and
`ENABLE_REFLECTION` with the environment variables above to make it act more
like an assistant.

### Operation modes and approvals

Choose how assertive the assistant should be:

- `AGENT_OPERATION_MODE=guided` (default) trusts the agent to act when it has a
  clear plan but will pause for approval if destructive verbs are detected or if
  a tool is explicitly gated.
- `AGENT_OPERATION_MODE=exploratory` treats the request as off-map and requests
  confirmation before running plans unless `AGENT_EXPLORATION_AUTO_APPROVE=true`
  is set.

Additional tuning knobs:

- `AGENT_APPROVAL_TOOLS="ToolA,ToolB"` gates those tools behind approval.
- `AGENT_APPROVAL_KEYWORDS="reset,drop table"` augments the built-in delete
  verbs so you can catch domain-specific risky language.

When a gate is hit, the CLI and voice loop show the proposed steps and ask for a
`y/N` confirmation before proceeding.

## TypeScript agent

Install dependencies and start the Node-based agent:

```bash
npm install
npm start
```

For development guidelines, consult [AGENTS.md](../AGENTS.md).

## Metrics stack

Generate a `.env` with strong credentials (run `./docker/gen-env.sh` or copy
`.env.example` and edit), then start Prometheus, Alertmanager, Grafana, and
Jaeger with the `metrics` profile:

```bash
./docker/gen-env.sh               # generate .env with random secrets
# or
cp .env.example .env              # edit values manually
docker compose -f docker/docker-compose.yml --profile metrics up
```

Grafana listens on port 3001, Prometheus on 9090, Alertmanager on 9093, and the
Jaeger UI on 16686. These services use the credentials supplied in `.env` and
include a sample alert rule. Postgres (5432) and MariaDB (3306) are bound to
127.0.0.1 for local access only. For production, place a TLS-terminating proxy
with authentication in front of all HTTP services.


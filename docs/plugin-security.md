# Plugin security and sandboxing

Plugins execute in a restricted subprocess to limit the impact of untrusted code.
The sandbox imposes basic CPU and memory limits and isolates plugin state from
 the main agent runtime. Each plugin declares Pydantic models for its expected
 input and output. Incoming arguments are validated against the input model
 before use, and results are validated against the output model before returning
 to the caller. Invalid or unsafe data causes the plugin to raise an error.

Developers writing plugins should rely on these models for validation and avoid
 mutating global state. Long running or resource intensive operations should be
 avoided because the sandboxed process has tight limits.

For details on creating plugins see the [quick start](quickstart.md).

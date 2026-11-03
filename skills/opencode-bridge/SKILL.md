---
name: opencode-bridge
version: 1.0.0
author: sarvesh173
license: MIT
description: Connect, supervise, and link OpenCode CLI sessions and agents with real-time status.
metadata:
  hermes:
    tags: [opencode, cli-agent, live-linking, session-management, delegation]
    related_skills: [autonomous-ai-agents/opencode, apple-agent-drilldown-architecture]
---

# OpenCode Plugin for TALOS

Hermes Agent integration for OpenCode (https://github.com/opencode-ai/opencode).
Provides programmatic session inspection, background server telemetry, and automated periodic live linking.

## 1. Capabilities & Workflow

- **Direct Database Inspection**: Reads `session_v2` and `session_message` from `~/.local/share/opencode/opencode.db` using read-only WAL connections without locking or pausing running agents.
- **Service Telemetry**: Probes `opencode service status` to verify running daemon endpoint (`http://127.0.0.1:49374`).
- **Periodic Live Linking**: Emits synchronized JSON state to `~/.hermes/opencode_live_state.json` every 30 to 60 seconds.
- **Agent Delegation**: Runs tasks directly using `opencode run "<prompt>" --model <model> --thinking`.

## 2. CLI Commands

```bash
# List all active & completed OpenCode sessions
python3 opencode_bridge.py --list

# Output consolidated real-time state as JSON
python3 opencode_bridge.py --status

# Launch live 30-second linking loop
python3 opencode_bridge.py --sync --interval 30

# Delegate a task to an OpenCode agent
python3 opencode_bridge.py --run "Refactor UI state" --model "opencode/beam-free"
```

## 3. Real-Time Status Schema

```json
{
  "timestamp": 1793725930,
  "service": {
    "status": "online",
    "endpoint": "http://127.0.0.1:49374"
  },
  "is_agent_running": false,
  "total_sessions": 15,
  "latest_session": {
    "id": "ses_e5dcc117fffePxuWJE6NrZxZhE",
    "title": "LandingScreen 3-tier navigation design",
    "directory": "/home/kira/talos",
    "model": "beam-free",
    "status": "Completed",
    "turns": 20,
    "timestamp": "38m ago"
  }
}
```

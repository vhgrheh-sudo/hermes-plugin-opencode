# hermes-plugin-opencode

> OpenCode CLI Bridge & Real-Time Session Integration for Hermes Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Plugin%20v1-7C4DFF.svg)](https://hermes-agent.nousresearch.com)
[![OpenCode](https://img.shields.io/badge/OpenCode-CLI-2563EB.svg)](https://github.com/opencode-ai/opencode)

`hermes-plugin-opencode` bridges [OpenCode](https://github.com/opencode-ai/opencode) CLI with [Hermes Agent](https://github.com/NousResearch/hermes-agent). It provides real-time session tracking, live agent status linking (30s/60s intervals), and direct task delegation.

---

## Features

- ⚡ **Zero-Latency Session Tracking**: Inspects OpenCode SQLite database (`session_v2`, `session_message`) with read-only WAL mode.
- 🔄 **Periodic Live Linking**: Continuously updates `~/.hermes/opencode_live_state.json` every 30 or 60 seconds with active turn counts, timestamps, and model telemetry.
- 🤖 **Multi-Model Agent Execution**: Run tasks headlessly with `--model opencode/pulse-alpha-free`, `beam-free`, or custom providers.
- 📱 **Mobile & Dashboard Ready**: Exposes structured JSON ready for TALOS Android Hub and web telemetry dashboards.

---

## Installation

### 1. Clone into your Hermes workspace
```bash
git clone https://github.com/vhgrheh-sudo/hermes-plugin-opencode.git ~/.hermes/plugins/opencode-bridge
```

### 2. Verify OpenCode CLI
Ensure `opencode` is installed and on your PATH:
```bash
opencode --version
```

---

## Usage

### List Sessions
```bash
python3 opencode_bridge.py --list
```

### Query Live Status
```bash
python3 opencode_bridge.py --status
```

### Start 30-Second Real-Time Linking Daemon
```bash
python3 opencode_bridge.py --sync --interval 30
```

### Delegate Task to OpenCode
```bash
python3 opencode_bridge.py --run "Audit Compose state hoisting" --model "opencode/beam-free"
```

---

## Architecture

```text
[ Hermes Agent / TALOS App ]
             │
      (Every 30s Poll)
             ▼
[ hermes-plugin-opencode ] ──── (Read-Only WAL) ────► [ ~/.local/share/opencode/opencode.db ]
             │
      (Subprocess IPC)
             ▼
[ OpenCode CLI Server ] (http://127.0.0.1:49374)
```

---

## License

MIT © sarvesh173

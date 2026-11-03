#!/usr/bin/env python3
"""OpenCode CLI Bridge & Real-Time Session Integration for Hermes Agent.

Provides direct linking, session enumeration, process supervision,
and real-time live polling for OpenCode CLI (https://github.com/opencode-ai/opencode).
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

OPENCODE_DB_PATH = os.path.expanduser("~/.local/share/opencode/opencode.db")
LIVE_STATE_PATH = os.path.expanduser("~/.hermes/opencode_live_state.json")


def format_relative_time(epoch_ms: int) -> str:
    """Formats epoch milliseconds into human-readable relative time."""
    now_ms = int(time.time() * 1000)
    diff_sec = max(0, (now_ms - epoch_ms) // 1000)

    if diff_sec < 60:
        return "Just now"
    elif diff_sec < 3600:
        mins = diff_sec // 60
        return f"{mins}m ago"
    elif diff_sec < 86400:
        hours = diff_sec // 3600
        return f"{hours}h ago"
    else:
        days = diff_sec // 86400
        return f"{days}d ago"


def get_opencode_sessions(limit: int = 30) -> List[Dict[str, Any]]:
    """Reads real-time sessions directly from OpenCode SQLite database."""
    if not os.path.exists(OPENCODE_DB_PATH):
        return []

    uri = f"file:{OPENCODE_DB_PATH}?mode=ro"
    sessions = []

    try:
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
        cursor = conn.cursor()

        # Query latest session_v2 rows joined with message count
        query = """
            SELECT 
                s.id,
                COALESCE(NULLIF(s.title, ''), 'Interactive Session') as title,
                s.directory,
                s.model,
                s.time_created,
                s.time_updated,
                s.tokens_input,
                s.tokens_output,
                COUNT(m.id) as turns_count
            FROM session_v2 s
            LEFT JOIN session_message m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.time_updated DESC
            LIMIT ?;
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        now_ms = int(time.time() * 1000)

        for row in rows:
            sid, title, directory, model_raw, t_created, t_updated, in_tok, out_tok, turns = row

            model_id = "default"
            if model_raw:
                try:
                    m_data = json.loads(model_raw)
                    model_id = m_data.get("id", "default")
                except Exception:
                    model_id = str(model_raw)

            # Active if touched in the last 15 minutes
            is_active = (now_ms - t_updated) < (15 * 60 * 1000)

            sessions.append({
                "id": sid,
                "title": title,
                "directory": directory,
                "model": model_id,
                "status": "Active" if is_active else "Completed",
                "turns": max(1, turns),
                "timestamp": format_relative_time(t_updated),
                "time_updated": t_updated,
                "time_created": t_created,
                "tokens_input": in_tok,
                "tokens_output": out_tok
            })

        conn.close()
    except Exception as e:
        print(f"[OpenCodeBridge] Error reading database: {e}", file=sys.stderr)

    return sessions


def get_opencode_service_status() -> Dict[str, Any]:
    """Checks the background OpenCode daemon status and web API endpoint."""
    try:
        res = subprocess.run(["opencode", "service", "status"], capture_output=True, text=True, timeout=5)
        endpoint = res.stdout.strip()
        is_running = "http" in endpoint
        return {
            "status": "online" if is_running else "offline",
            "endpoint": endpoint if is_running else None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_active_agent_summary() -> Dict[str, Any]:
    """Returns a consolidated real-time state of OpenCode CLI."""
    sessions = get_opencode_sessions(limit=15)
    service = get_opencode_service_status()

    # Identify currently running background processes
    active_process = False
    try:
        p_check = subprocess.run(["pgrep", "-f", "opencode run"], capture_output=True, text=True)
        active_process = bool(p_check.stdout.strip())
    except Exception:
        pass

    state = {
        "timestamp": int(time.time()),
        "service": service,
        "is_agent_running": active_process,
        "total_sessions": len(sessions),
        "latest_session": sessions[0] if sessions else None,
        "sessions": sessions
    }

    # Atomically write to live state file
    try:
        os.makedirs(os.path.dirname(LIVE_STATE_PATH), exist_ok=True)
        tmp_path = LIVE_STATE_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, LIVE_STATE_PATH)
    except Exception as e:
        print(f"[OpenCodeBridge] Failed to write live state: {e}", file=sys.stderr)

    return state


def run_opencode_task(prompt: str, model: str = "opencode/beam-free", directory: Optional[str] = None, thinking: bool = True) -> int:
    """Invokes OpenCode CLI with the specified prompt and options."""
    cmd = ["opencode", "run", prompt, "--model", model]
    if thinking:
        cmd.append("--thinking")
    if directory:
        cmd.append(directory)

    print(f"[OpenCodeBridge] Running: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode


def start_live_sync_daemon(interval: int = 30):
    """Background loop that polls OpenCode state every N seconds."""
    print(f"[OpenCodeBridge] Starting live sync daemon (interval={interval}s)...")
    while True:
        try:
            get_active_agent_summary()
        except Exception as e:
            print(f"[OpenCodeBridge] Sync loop error: {e}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCode CLI Bridge for Hermes Agent")
    parser.add_argument("--list", action="store_true", help="List active OpenCode sessions")
    parser.add_argument("--status", action="store_true", help="Show OpenCode daemon & live status")
    parser.add_argument("--sync", action="store_true", help="Run background live linking loop (30s)")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds")
    parser.add_argument("--run", type=str, help="Prompt to execute via opencode run")
    parser.add_argument("--model", type=str, default="opencode/beam-free", help="Model identifier")

    args = parser.parse_args()

    if args.list:
        sess = get_opencode_sessions()
        print(f"Found {len(sess)} OpenCode sessions:")
        for s in sess:
            print(f"  [{s['id']}] {s['title']} ({s['turns']} turns, {s['timestamp']}) - {s['status']}")
    elif args.status:
        st = get_active_agent_summary()
        print(json.dumps(st, indent=2))
    elif args.sync:
        start_live_sync_daemon(args.interval)
    elif args.run:
        code = run_opencode_task(args.run, args.model)
        sys.exit(code)
    else:
        # Default action: print status summary
        st = get_active_agent_summary()
        print(f"OpenCode Status: {st['service']['status']}")
        print(f"Active Agent Running: {st['is_agent_running']}")
        print(f"Total Sessions: {st['total_sessions']}")
        if st['latest_session']:
            print(f"Latest: {st['latest_session']['title']} ({st['latest_session']['timestamp']})")

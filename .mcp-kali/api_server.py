#!/usr/bin/env python3
"""Kali MCP API Server — runs inside the Kali VM on port 5000."""

import subprocess
import json
import shutil
from flask import Flask, request, jsonify

app = Flask(__name__)

TIMEOUT = 300


def run_cmd(cmd, timeout=TIMEOUT):
    """Execute a shell command and return result dict."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": r.returncode == 0,
            "exit_code": r.returncode,
            "stdout": r.stdout[-5000:] if r.stdout else "",
            "stderr": r.stderr[-5000:] if r.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "exit_code": -1, "stdout": "", "stderr": f"Command timed out after {timeout}s"}


def check_tools():
    """Check which tools are available."""
    tools = ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "msfconsole", "whatweb", "wafw00f", "sslscan", "dnsrecon"]
    status = {}
    for t in tools:
        status[t] = shutil.which(t) is not None
    return status


@app.route("/health", methods=["GET"])
def health():
    tools_status = check_tools()
    essential = ["nmap", "gobuster", "nikto", "sqlmap", "hydra"]
    return jsonify({
        "status": "healthy",
        "all_essential_tools_available": all(tools_status.get(t) for t in essential),
        "tools_status": tools_status,
    })


@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json()
    cmd = data.get("command", "")
    if not cmd:
        return jsonify({"success": False, "stderr": "No command provided"})
    return jsonify(run_cmd(cmd))


def build_tool_cmd(tool, data):
    """Build CLI command string from tool name and args."""
    builders = {
        "nmap": lambda d: f"nmap {d.get('scan_type', '-sV')} {d.get('ports', '')} {d.get('additional_args', '')} {d.get('target', '')}".strip(),
        "gobuster": lambda d: f"gobuster {d.get('mode', 'dir')} -u {d.get('url', '')} -w {d.get('wordlist', '/usr/share/wordlists/dirb/common.txt')} {d.get('additional_args', '')}".strip(),
        "dirb": lambda d: f"dirb {d.get('url', '')} {d.get('wordlist', '/usr/share/wordlists/dirb/common.txt')} {d.get('additional_args', '')}".strip(),
        "nikto": lambda d: f"nikto -h {d.get('target', '')} {d.get('additional_args', '')}".strip(),
        "sqlmap": lambda d: f"sqlmap -u {d.get('url', '')} {d.get('additional_args', '')} {f'--data={d[\"data\"]}' if d.get('data') else ''}".strip(),
        "hydra": lambda d: f"hydra -l {d.get('username', '')} -P {d.get('password_file', '')} {d.get('additional_args', '')} {d.get('target', '')} {d.get('service', '')}".strip(),
        "john": lambda d: f"john --wordlist={d.get('wordlist', '/usr/share/wordlists/rockyou.txt')} {d.get('format_type', '')} {d.get('additional_args', '')} {d.get('hash_file', '')}".strip(),
        "metasploit": lambda d: f"msfconsole -q -x 'use {d.get('module', '')}; run; exit'",
    }
    builder = builders.get(tool)
    return builder(data) if builder else ""


@app.route("/api/tools/<tool>", methods=["POST"])
def api_tool(tool):
    data = request.get_json() or {}
    cmd = build_tool_cmd(tool, data)
    if not cmd:
        return jsonify({"success": False, "stderr": f"Unknown tool: {tool}"})
    return jsonify(run_cmd(cmd, timeout=TIMEOUT))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

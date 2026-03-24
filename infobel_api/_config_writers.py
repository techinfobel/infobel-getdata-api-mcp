"""Per-agent config writers for infobel-mcp add <agent>."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# TOML helpers
# ---------------------------------------------------------------------------

def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    else:
        import tomli  # type: ignore[import]
        with open(path, "rb") as f:
            return tomli.load(f)


def _write_toml(path: Path, data: dict) -> None:
    import tomli_w  # type: ignore[import]
    tmp = path.with_suffix(".toml.tmp")
    with open(tmp, "wb") as f:
        tomli_w.dump(data, f)
    tmp.replace(path)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Deep merge helper
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Public writers
# ---------------------------------------------------------------------------

def write_claude(path: Path, username: str, password: str, python_executable: str) -> None:
    """Write/merge the infobel block into a Claude JSON config file.

    Global target: ~/.claude.json
    Local target:  <project>/.mcp.json
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_json(path)
    block: dict[str, Any] = {
        "mcpServers": {
            "infobel": {
                "type": "stdio",
                "command": python_executable,
                "args": ["-m", "infobel_api.mcp_server"],
                "env": {
                    "INFOBEL_USERNAME": username,
                    "INFOBEL_PASSWORD": password,
                },
            }
        }
    }
    merged = _deep_merge(existing, block)
    _write_json(path, merged)


def write_gemini(path: Path, username: str, password: str, python_executable: str) -> None:
    """Write/merge the infobel block into a Gemini JSON settings file.

    Global target: ~/.gemini/settings.json
    Local target:  <project>/.gemini/settings.json
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_json(path)
    block: dict[str, Any] = {
        "mcpServers": {
            "infobel": {
                "command": python_executable,
                "args": ["-m", "infobel_api.mcp_server"],
                "env": {
                    "INFOBEL_USERNAME": username,
                    "INFOBEL_PASSWORD": password,
                },
            }
        }
    }
    merged = _deep_merge(existing, block)
    _write_json(path, merged)


def write_codex(path: Path, username: str, password: str, python_executable: str) -> None:
    """Write/merge the infobel block into a Codex TOML config file.

    Global target: ~/.codex/config.toml
    Local target:  <project>/.codex/config.toml
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_toml(path)
    block: dict[str, Any] = {
        "mcp_servers": {
            "infobel": {
                "command": python_executable,
                "args": ["-m", "infobel_api.mcp_server"],
                "env": {
                    "INFOBEL_USERNAME": username,
                    "INFOBEL_PASSWORD": password,
                },
            }
        }
    }
    merged = _deep_merge(existing, block)
    _write_toml(path, merged)

"""Tests for infobel-mcp CLI and config writers."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _read_toml(path: Path) -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    else:
        import tomli
        with open(path, "rb") as f:
            return tomli.load(f)


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

class TestCLIDispatch:
    def test_no_args_calls_mcp_main(self):
        """When called with no args, main() delegates to mcp_server.main()."""
        with patch("sys.argv", ["infobel-mcp"]):
            with patch("infobel_api.mcp_server.main") as mock_mcp:
                from infobel_api.cli import main
                main()
                mock_mcp.assert_called_once()


# ---------------------------------------------------------------------------
# Config writers — Claude
# ---------------------------------------------------------------------------

class TestWriteClaude:
    def test_writes_correct_structure(self, tmp_path):
        from infobel_api._config_writers import write_claude
        target = tmp_path / ".mcp.json"
        write_claude(target, "user1", "pass1", "/usr/bin/python3")

        data = _read_json(target)
        mcp = data["mcpServers"]["infobel"]
        assert mcp["type"] == "stdio"
        assert mcp["command"] == "/usr/bin/python3"
        assert mcp["args"] == ["-m", "infobel_api.mcp_server"]
        assert mcp["env"]["INFOBEL_USERNAME"] == "user1"
        assert mcp["env"]["INFOBEL_PASSWORD"] == "pass1"

    def test_idempotent_merge_preserves_other_servers(self, tmp_path):
        from infobel_api._config_writers import write_claude
        target = tmp_path / ".mcp.json"

        # Pre-populate with another server
        target.write_text(json.dumps({"mcpServers": {"other": {"command": "other-cmd"}}}))

        write_claude(target, "user1", "pass1", "/usr/bin/python3")
        data = _read_json(target)

        # Both servers present
        assert "other" in data["mcpServers"]
        assert "infobel" in data["mcpServers"]

    def test_idempotent_second_write_no_duplicates(self, tmp_path):
        from infobel_api._config_writers import write_claude
        target = tmp_path / ".mcp.json"
        write_claude(target, "user1", "pass1", "/usr/bin/python3")
        write_claude(target, "user1", "pass1", "/usr/bin/python3")

        data = _read_json(target)
        # Still only one infobel entry
        assert len([k for k in data["mcpServers"] if k == "infobel"]) == 1

    def test_creates_parent_dirs(self, tmp_path):
        from infobel_api._config_writers import write_claude
        target = tmp_path / "deep" / "nested" / ".mcp.json"
        write_claude(target, "u", "p", "/usr/bin/python3")
        assert target.exists()


# ---------------------------------------------------------------------------
# Config writers — Codex
# ---------------------------------------------------------------------------

class TestWriteCodex:
    def test_writes_correct_toml_structure(self, tmp_path):
        from infobel_api._config_writers import write_codex
        target = tmp_path / ".codex" / "config.toml"
        write_codex(target, "user2", "pass2", "/usr/bin/python3")

        data = _read_toml(target)
        srv = data["mcp_servers"]["infobel"]
        assert srv["command"] == "/usr/bin/python3"
        assert srv["args"] == ["-m", "infobel_api.mcp_server"]
        assert srv["env"]["INFOBEL_USERNAME"] == "user2"
        assert srv["env"]["INFOBEL_PASSWORD"] == "pass2"

    def test_idempotent_merge_preserves_other_servers(self, tmp_path):
        import tomli_w
        from infobel_api._config_writers import write_codex
        target = tmp_path / "config.toml"

        # Pre-populate
        existing = {"mcp_servers": {"other": {"command": "other-cmd"}}}
        with open(target, "wb") as f:
            tomli_w.dump(existing, f)

        write_codex(target, "user2", "pass2", "/usr/bin/python3")
        data = _read_toml(target)
        assert "other" in data["mcp_servers"]
        assert "infobel" in data["mcp_servers"]

    def test_creates_parent_dirs(self, tmp_path):
        from infobel_api._config_writers import write_codex
        target = tmp_path / ".codex" / "config.toml"
        write_codex(target, "u", "p", "/usr/bin/python3")
        assert target.exists()


# ---------------------------------------------------------------------------
# Config writers — Gemini
# ---------------------------------------------------------------------------

class TestWriteGemini:
    def test_writes_real_credentials(self, tmp_path):
        from infobel_api._config_writers import write_gemini
        target = tmp_path / ".gemini" / "settings.json"
        write_gemini(target, "myuser", "mypass", "/usr/bin/python3")

        data = _read_json(target)
        srv = data["mcpServers"]["infobel"]
        assert srv["command"] == "/usr/bin/python3"
        assert srv["args"] == ["-m", "infobel_api.mcp_server"]
        assert srv["env"]["INFOBEL_USERNAME"] == "myuser"
        assert srv["env"]["INFOBEL_PASSWORD"] == "mypass"

    def test_writes_env_var_placeholders_when_passed(self, tmp_path):
        from infobel_api._config_writers import write_gemini
        target = tmp_path / ".gemini" / "settings.json"
        write_gemini(target, "${INFOBEL_USERNAME}", "${INFOBEL_PASSWORD}", "/usr/bin/python3")

        data = _read_json(target)
        srv = data["mcpServers"]["infobel"]
        assert srv["env"]["INFOBEL_USERNAME"] == "${INFOBEL_USERNAME}"
        assert srv["env"]["INFOBEL_PASSWORD"] == "${INFOBEL_PASSWORD}"

    def test_idempotent_merge(self, tmp_path):
        from infobel_api._config_writers import write_gemini
        target = tmp_path / "settings.json"
        target.write_text(json.dumps({"mcpServers": {"other": {"command": "other"}}}))
        write_gemini(target, "u", "p", "/usr/bin/python3")
        data = _read_json(target)
        assert "other" in data["mcpServers"]
        assert "infobel" in data["mcpServers"]


# ---------------------------------------------------------------------------
# CLI --local path resolution
# ---------------------------------------------------------------------------

class TestLocalPathResolution:
    def test_local_flag_no_path_uses_cwd(self, tmp_path, monkeypatch):
        """--local with no path writes to cwd."""
        monkeypatch.chdir(tmp_path)
        from infobel_api.cli import _resolve_target
        result = _resolve_target("claude", "")  # empty string = cwd
        assert result == tmp_path / ".mcp.json"

    def test_local_flag_with_absolute_path(self, tmp_path):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("claude", str(tmp_path))
        assert result == tmp_path / ".mcp.json"

    def test_global_claude(self):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("claude", None)
        assert result == Path.home() / ".claude.json"

    def test_global_codex(self):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("codex", None)
        assert result == Path.home() / ".codex" / "config.toml"

    def test_global_gemini(self):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("gemini", None)
        assert result == Path.home() / ".gemini" / "settings.json"

    def test_local_codex(self, tmp_path):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("codex", str(tmp_path))
        assert result == tmp_path / ".codex" / "config.toml"

    def test_local_gemini(self, tmp_path):
        from infobel_api.cli import _resolve_target
        result = _resolve_target("gemini", str(tmp_path))
        assert result == tmp_path / ".gemini" / "settings.json"

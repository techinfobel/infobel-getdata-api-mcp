"""CLI entry point for infobel-mcp.

No args  → MCP server mode (stdio, called by agent hosts).
With args → CLI mode (infobel-mcp add <agent> ...).
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path


def _resolve_target(agent: str, local: str | None) -> Path:
    """Return the config file path for the given agent and --local value."""
    if local is None:
        # Global (user-home) locations
        home = Path.home()
        if agent == "claude":
            return home / ".claude.json"
        elif agent == "codex":
            return home / ".codex" / "config.toml"
        elif agent == "gemini":
            return home / ".gemini" / "settings.json"
    else:
        base = Path(local) if local else Path.cwd()
        if agent == "claude":
            return base / ".mcp.json"
        elif agent == "codex":
            return base / ".codex" / "config.toml"
        elif agent == "gemini":
            return base / ".gemini" / "settings.json"
    raise ValueError(f"Unknown agent: {agent}")


def _get_credentials(
    username: str | None,
    password: str | None,
    use_env_vars: bool,
) -> tuple[str, str]:
    """Resolve credentials from flags, env vars, or interactive prompts."""
    if use_env_vars:
        return "${INFOBEL_USERNAME}", "${INFOBEL_PASSWORD}"

    resolved_username = username or os.environ.get("INFOBEL_USERNAME") or getpass.getpass("Infobel username: ")
    resolved_password = password or os.environ.get("INFOBEL_PASSWORD") or getpass.getpass("Infobel password: ")
    return resolved_username, resolved_password


def _detect_python_executable() -> str:
    """Return the absolute path to the Python interpreter running this process.

    This is always the correct interpreter to use in MCP configs — it is the
    Python that has infobel_api installed, regardless of whether the user is
    in a venv, conda environment, pyenv, or system Python on any platform.
    """
    return sys.executable


def _cmd_add(args: argparse.Namespace) -> None:
    from infobel_api._config_writers import write_claude, write_codex, write_gemini

    agent = args.agent
    local: str | None = args.local  # None = global; "" or path = local

    target = _resolve_target(agent, local)

    use_env = args.use_env_vars
    username, password = _get_credentials(args.username, args.password, use_env)

    python_executable = _detect_python_executable()
    print(f"Using Python: {python_executable}")

    if agent == "claude":
        write_claude(target, username, password, python_executable)
    elif agent == "codex":
        write_codex(target, username, password, python_executable)
    elif agent == "gemini":
        write_gemini(target, username, password, python_executable)
    else:
        print(f"Unknown agent: {agent}", file=sys.stderr)
        sys.exit(1)

    print(f"Written: {target}")


def main() -> None:
    if len(sys.argv) == 1:
        # No args — MCP server mode
        from infobel_api.mcp_server import main as mcp_main
        mcp_main()
        return

    parser = argparse.ArgumentParser(
        prog="infobel-mcp",
        description="Infobel MCP server and agent configurator",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser(
        "add",
        help="Configure infobel-mcp into an agent host",
    )
    add_parser.add_argument(
        "agent",
        choices=["claude", "codex", "gemini"],
        help="Agent host to configure",
    )
    add_parser.add_argument(
        "--local",
        nargs="?",
        const="",  # --local with no value → cwd
        default=None,  # not supplied → global
        metavar="PATH",
        help="Write to project-local config (default: cwd). Optionally supply a path.",
    )
    add_parser.add_argument("--username", metavar="TEXT", help="Infobel username")
    add_parser.add_argument("--password", metavar="TEXT", help="Infobel password")
    add_parser.add_argument(
        "--use-env-vars",
        action="store_true",
        help="Write ${INFOBEL_USERNAME}/${INFOBEL_PASSWORD} placeholders",
    )

    args = parser.parse_args()

    if args.command == "add":
        _cmd_add(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

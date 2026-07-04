# infobel-api-mcp

Python client and MCP server for the [Infobel](https://www.infobelpro.com/) GetData API.

---

## Installation

From PyPI:

```bash
pip install infobel-api-mcp
```

For local development:

```bash
pip install -e .
```

Requires Python 3.10+.

---

## Quick start — configure your agent

After installing, run one command to wire infobel-mcp into your agent host:

```bash
# User-global config (prompts for credentials)
infobel-mcp add claude       # writes ~/.claude.json
infobel-mcp add codex        # writes ~/.codex/config.toml
infobel-mcp add gemini       # writes ~/.gemini/settings.json (uses env var placeholders)

# Project-local config (cwd)
infobel-mcp add claude --local
infobel-mcp add codex  --local
infobel-mcp add gemini --local

# Project-local config at a specific path
infobel-mcp add claude --local /path/to/project

# Skip the interactive prompts
infobel-mcp add claude --username myuser --password mypass

# Write ${INFOBEL_USERNAME}/${INFOBEL_PASSWORD} placeholders instead of literal creds
infobel-mcp add claude --use-env-vars
```

After running the command, set your credentials as environment variables:

```bash
export INFOBEL_USERNAME="your-username"
export INFOBEL_PASSWORD="your-password"
```

---

## Configuration

Set your credentials as environment variables:

```bash
export INFOBEL_USERNAME="your-username"
export INFOBEL_PASSWORD="your-password"
```

Or pass them directly when creating a client:

```python
from infobel_api import InfobelClient

client = InfobelClient(username="your-username", password="your-password")
```

---

## Python client

### Basic search

```python
from infobel_api import InfobelClient

with InfobelClient() as client:
    result = client.search.search(country_codes="GB", business_name="Acme")

    print(result["counts"]["total"])       # total matching businesses
    print(result["firstPageRecords"])      # [] by default
```

`return_first_page` defaults to `False`, so `search()` returns counts and a `searchId` without embedding records unless you explicitly opt in.

### Get specific fields (recommended for large result sets)

```python
with InfobelClient() as client:
    # Start a search
    result = client.search.search(
        country_codes="US",
        business_name="Tesla",
    )
    search_id = result["searchId"]

    # Fetch page 1 with only the fields you need
    page = client.search.post_records(
        search_id,
        page=1,
        fields=["uniqueID", "businessName", "phone", "email", "city"],
    )
    for record in page["records"]:
        print(record)

    # Fetch page 2
    page2 = client.search.post_records(search_id, page=2, fields=["uniqueID", "businessName"])
```

### Fetch a full record by unique ID

```python
with InfobelClient() as client:
    record = client.record.get(country_code="US", unique_id="0226550061")
    print(record["businessName"], record["phone"])
```

### Other filters

```python
with InfobelClient() as client:
    # By national ID
    result = client.search.search(country_codes="BE", national_id="0123456789")

    # Businesses with email in a city
    result = client.search.search(
        country_codes="FR",
        city_names="Paris",
        has_email=True,
    )

    # Filter by employee count
    result = client.search.search(
        country_codes="DE",
        employees_total_from=50,
        employees_total_to=200,
    )
```

---

## MCP server

The package ships an [MCP](https://modelcontextprotocol.io/) server that exposes the Infobel API as tools for AI agents (Claude, etc.).

### Quick install for Claude Code

After installing the package, register the MCP server with:

```bash
infobel-mcp add claude
```

This automatically uses the Python executable that has the package installed, regardless of whether you are in a venv, conda environment, or using the system Python.

### Configure Claude Code manually

As of March 18, 2026, Claude Code stores MCP servers in:

- User scope: `~/.claude.json`
- Project scope: `/path/to/project/.mcp.json`

On Windows, `~/.claude.json` maps to your home directory, typically `%USERPROFILE%\\.claude.json`.

Add this to either file:

```json
{
  "mcpServers": {
    "infobel": {
      "type": "stdio",
      "command": "/path/to/your/python",
      "args": ["-m", "infobel_api.mcp_server"],
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

Replace `/path/to/your/python` with the Python executable that has `infobel-api-mcp` installed. To find it, run this inside the environment where the package is installed:

```bash
python -c "import sys; print(sys.executable)"
```

For a venv the path typically looks like `/path/to/project/venv/bin/python`. For conda it looks like `/opt/conda/envs/myenv/bin/python`. The `infobel-mcp add claude` command above handles this automatically.

### Configure Gemini CLI manually

Gemini CLI stores MCP servers in:

- User scope: `~/.gemini/settings.json`
- Project scope: `/path/to/project/.gemini/settings.json`

On Windows, `~/.gemini/settings.json` maps to your home directory, typically `%USERPROFILE%\\.gemini\\settings.json`.

Add this to the `settings.json` file:

```json
{
  "mcpServers": {
    "infobel": {
      "command": "/path/to/your/python",
      "args": ["-m", "infobel_api.mcp_server"],
      "env": {
        "INFOBEL_USERNAME": "${INFOBEL_USERNAME}",
        "INFOBEL_PASSWORD": "${INFOBEL_PASSWORD}"
      }
    }
  }
}
```

Replace `/path/to/your/python` with the Python executable that has `infobel-api-mcp` installed (see the note in the Claude Code section above). If your `settings.json` already contains other top-level keys, merge the `mcpServers` block into the existing file instead of replacing it.

### Configure Codex manually

Codex stores MCP servers in:

- User scope: `~/.codex/config.toml`
- Project scope: `/path/to/project/.codex/config.toml`

On Windows, `~/.codex/config.toml` maps to your home directory, typically `%USERPROFILE%\\.codex\\config.toml`.

Add this to `config.toml`:

```toml
[mcp_servers.infobel]
command = "/path/to/your/python"
args = ["-m", "infobel_api.mcp_server"]

[mcp_servers.infobel.env]
INFOBEL_USERNAME = "your-username"
INFOBEL_PASSWORD = "your-password"
```

Replace `/path/to/your/python` with the Python executable that has `infobel-api-mcp` installed (see the note in the Claude Code section above). Codex CLI and the Codex IDE extension share the same MCP configuration.

### Claude Desktop (one-click extension)

Claude Desktop is a separate app from Claude Code and uses a different config. The easiest path for end users is the bundled **Desktop Extension** (`.mcpb`): no Python install, no manual JSON, no PATH setup. The user double-clicks the bundle, Claude Desktop prompts for the Infobel username and password, and the tools appear.

**Install (for users):**

1. Download `infobel-getdata.mcpb` from the [releases page](https://github.com/techinfobel/infobel-getdata-api-mcp/releases).
2. Double-click it (or in Claude Desktop: **Settings → Extensions → Install Extension…**).
3. Enter your Infobel username and password in the dialog. The password is stored securely in the OS keychain.
4. Fully quit and reopen Claude Desktop. The Infobel tools are now available.

The bundle uses the MCPB `uv` server type — Claude Desktop runs [`uv`](https://docs.astral.sh/uv/) to resolve dependencies cross-platform at install time, so users do not need their own Python.

**Build the bundle (for maintainers):**

```bash
./build_mcpb.sh          # → dist/infobel-getdata.mcpb
```

Requires Node.js (the script invokes `npx @anthropic-ai/mcpb`). The manifest lives in `mcpb/manifest.json`; bump its `version` on each release. Attach the resulting `.mcpb` to a GitHub Release.

**Configure Claude Desktop manually** (alternative to the extension): edit the config file directly —

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "infobel": {
      "command": "/path/to/your/python",
      "args": ["-m", "infobel_api.mcp_server"],
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

Claude Desktop does not inherit your shell environment or expand `${VAR}` placeholders, so the `command` must be an absolute Python path and credentials must be literal values. Fully restart the app after editing.

### Available tools

| Tool | Description |
|------|-------------|
| `count_businesses` | Counts-only search with optional per-country breakdown (parallel) and zero-result diagnosis — preferred for "how many" questions |
| `resolve_categories` | Resolve keywords to category codes across all four systems in parallel, with known-conflation warnings |
| `resolve_location` | Resolve a place name to codes and the correct filter level (city vs province vs region) |
| `search_businesses` | Search by name, location, category, and more |
| `get_search_results` | Fetch additional pages from a previous search |
| `get_record` | Get a full business record by unique ID |
| `get_record_partial` | Get a lightweight record by unique ID |
| `get_categories_infobel` | Browse Infobel category tree |
| `get_categories_international` | Browse ISIC categories |
| `get_categories_local` | Browse local/national categories |
| `get_locations_cities` | List cities for a country |
| `get_locations_regions` | List regions for a country |
| `get_locations_provinces` | List provinces for a country |
| `get_available_countries` | List all available countries |
| `get_languages` | List available display languages |
| `test_connection` | Verify API connectivity |

### Example MCP interaction

Once configured, you can ask Claude things like:

> "Find all Italian restaurants in Brussels with a phone number."

Claude will call `search_businesses` with the right filters and return structured results. You tell it which fields you care about:

> "Search for Google offices in the US — I only need the business name, address, and phone number."

The `record_fields` parameter controls what comes back (pass `[]` for counts only):

```
search_businesses(
  country_codes=["US"],
  business_name=["Google"],
  record_fields=["businessName", "address1", "city", "phone"]
)
```

To get more pages, use the `searchId` from the first call:

```
get_search_results(
  search_id=12345,
  page=2,
  record_fields=["businessName", "address1", "city", "phone"]
)
```

### Counting and resolving (recommended flow)

For sizing questions, prefer the counts-only task tool. With `group_by_country=True`
the per-country searches run in parallel server-side:

> "How many restaurants with a website do we have in France, Germany and Belgium?"

```
resolve_categories(keywords=["restaurant"])            # pick the right codes first
count_businesses(
  country_codes=["FR", "DE", "BE"],
  infobel_codes=["..."],
  has_website=True,
  group_by_country=True
)
```

`resolve_location` tells you which filter level a place name belongs to (a city
filter counts the city only; a province/region filter counts the whole area):

```
resolve_location(text="São Paulo", country_code="BR")
```

When a search matches nothing, the response includes a `diagnosis` block that
re-runs the search without one filter group at a time (in parallel, counts-only)
and reports which filter group is likely blocking the results.

---

## Error handling

```python
from infobel_api import InfobelAPIError, AuthenticationError, RateLimitError, NetworkError

try:
    result = client.search.search(country_codes="GB", business_name="Acme")
except AuthenticationError:
    print("Invalid credentials")
except RateLimitError:
    print("Rate limited — retries are automatic")
except NetworkError:
    print("Connection issue")
except InfobelAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

The client handles rate limiting and retries automatically.

---

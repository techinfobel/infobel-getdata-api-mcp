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
claude mcp add infobel -- infobel-mcp
```

Once the package is published on PyPI, you can also skip the prior `pip install` step and run it through `uvx`:

```bash
claude mcp add infobel -- uvx infobel-api
```

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
      "command": "infobel-mcp",
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

If the script is not on your `PATH`, use the full path to the installed `infobel-mcp` executable instead.

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
      "command": "infobel-mcp",
      "env": {
        "INFOBEL_USERNAME": "${INFOBEL_USERNAME}",
        "INFOBEL_PASSWORD": "${INFOBEL_PASSWORD}"
      }
    }
  }
}
```

If your `settings.json` already contains other top-level keys, merge the `mcpServers` block into the existing file instead of replacing it.

### Configure Codex manually

Codex stores MCP servers in:

- User scope: `~/.codex/config.toml`
- Project scope: `/path/to/project/.codex/config.toml`

On Windows, `~/.codex/config.toml` maps to your home directory, typically `%USERPROFILE%\\.codex\\config.toml`.

Add this to `config.toml`:

```toml
[mcp_servers.infobel]
command = "infobel-mcp"

[mcp_servers.infobel.env]
INFOBEL_USERNAME = "your-username"
INFOBEL_PASSWORD = "your-password"
```

Codex CLI and the Codex IDE extension share the same MCP configuration.

### Available tools

| Tool | Description |
|------|-------------|
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

## Publishing checklist

The package is designed to be published to PyPI and used in two ways:

```bash
pip install infobel-api
claude mcp add infobel -- infobel-mcp
```

or, after publication:

```bash
claude mcp add infobel -- uvx infobel-api
```

Before each release:

1. Activate the local environment.
   Run `source venv/bin/activate`.
2. Build and validate distributions.
   Run `python -m build` and `python -m twine check dist/*`.
3. Test the wheel locally.
   Install the built wheel in a clean environment and verify `infobel-mcp` is available.
4. Publish to TestPyPI or PyPI through the GitHub Actions release workflow.

Example console script metadata:

```toml
[project.scripts]
infobel-mcp = "infobel_api.mcp_server:main"
```

After that, Claude/MCP setup becomes simpler:

```json
{
  "mcpServers": {
    "infobel": {
      "command": "infobel-mcp",
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

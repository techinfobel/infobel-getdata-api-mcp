# infobel-api

Python client and MCP server for the [Infobel](https://www.infobelpro.com/) GetData API.

---

## Installation

```bash
pip install -e .
```

Requires Python 3.11+.

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
    print(result["firstPageRecords"][0])   # first record (all fields)
```

### Get specific fields (recommended for large result sets)

```python
with InfobelClient() as client:
    # Start a search
    result = client.search.search(
        country_codes="US",
        business_name="Tesla",
        return_first_page=False,  # skip embedding records in search response
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
        employees_total_from="50",
        employees_total_to="200",
    )
```

---

## MCP server

The package ships an [MCP](https://modelcontextprotocol.io/) server that exposes the Infobel API as tools for AI agents (Claude, etc.).

### Configure Claude Desktop

Add this to your `~/claude.json` or in your given project within `~/path-to-your-project/.mcp.json`:

```json
{
  "mcpServers": {
    "infobel": {
      "command": "python3",
      "args": ["-m", "infobel_api.mcp_server"],
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

If you installed into a virtual environment, use the full path to the Python binary:

```json
{
  "mcpServers": {
    "infobel": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "infobel_api.mcp_server"],
      "env": {
        "INFOBEL_USERNAME": "your-username",
        "INFOBEL_PASSWORD": "your-password"
      }
    }
  }
}
```

Restart Claude Desktop after saving the file. The Infobel tools will appear automatically.

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
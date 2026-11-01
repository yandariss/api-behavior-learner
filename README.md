# API Behavior Learner

[![Tests](https://github.com/yandariss/api-behavior-learner/actions/workflows/tests.yml/badge.svg)](https://github.com/yandariss/api-behavior-learner/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Reverse engineer REST APIs from HTTP traffic logs. Automatically detect endpoints, infer schemas, generate OpenAPI specs and documentation.

## Features

- **HTTP Traffic Analysis**: Parse HAR files from browser DevTools or proxies
- **Endpoint Detection**: Automatically group and pattern-match API endpoints
- **Schema Inference**: Deduce JSON schemas from response payloads
- **Static Asset Filtering**: Remove noise (favicon, CSS, JS, images)
- **Documentation Generation**: Create Markdown docs and OpenAPI 3.0 specs
- **Browser Automation**: Capture live traffic via Selenium + Chrome DevTools Protocol
- **LLM Integration**: Optional OpenAI integration for intelligent endpoint descriptions
- **No Dependencies on API Docs**: Works with undocumented, legacy, or proprietary APIs

## Installation

### Requirements
- Python 3.9+
- pip or poetry

### Quick Install

```bash
git clone https://github.com/yandariss/api-behavior-learner.git
cd api-behavior-learner
pip install -r requirements.txt
```

### Optional: For Browser Automation

```bash
pip install selenium webdriver-manager
```

### Optional: For LLM Integration

Set `OPENAI_API_KEY` in `.env`:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Quick Start

### 1. Basic Usage (No LLM)

```bash
python -m api_behavior_learner samples/sample.har --no-llm -o api-docs
```

Generates:
- `api-docs/api-docs.md` - Markdown documentation
- `api-docs/openapi.json` - OpenAPI 3.0 specification

### 2. With OpenAI Integration

```bash
# Set OPENAI_API_KEY in .env first
python -m api_behavior_learner samples/sample.har -o api-docs
```

LLM analyzes patterns and generates smarter descriptions.

### 3. Capture Live Traffic

```bash
python capture_har.py
```

Opens browser, navigates DummyJSON API endpoints, captures traffic to `samples/dummyjson.har`.

### 4. Custom Endpoints

Edit `capture_har.py` to change target URLs and endpoints.

## Usage Examples

### Command Line

```bash
# Basic analysis, no LLM
python -m api_behavior_learner api-traffic.har --no-llm -o docs

# With OpenAI LLM analysis
python -m api_behavior_learner api-traffic.har -o docs

# Specify output format
python -m api_behavior_learner api-traffic.har -f openapi -o specs

# Custom API title and version
python -m api_behavior_learner api-traffic.har --title "MyAPI" --version "2.0.0" -o docs
```

### Programmatic Usage

```python
from api_behavior_learner.har_parser import HARParser
from api_behavior_learner.grouper import EndpointGrouper
from api_behavior_learner.spec_generator import SpecGenerator
from api_behavior_learner.llm_analyzer import LLMAnalyzer

har_parser = HARParser('api-traffic.har')
transactions = har_parser.load()

grouper = EndpointGrouper(transactions)
endpoints = grouper.group()

analyzer = LLMAnalyzer()
spec_gen = SpecGenerator(analyzer)

markdown_docs = spec_gen.generate_markdown(endpoints)
openapi_spec = spec_gen.generate_openapi(endpoints, title="MyAPI", version="1.0.0")

print(markdown_docs)
```

## How It Works

### Architecture

```
Input (HAR File)
    ↓
[HARParser] → Extracts requests/responses, filters static assets
    ↓
[EndpointGrouper] → Groups by pattern, replaces IDs with {id}
    ↓
[SchemaInferrer] → Deduces JSON types from payloads
    ↓
[LLMAnalyzer] (optional) → Generates smart descriptions
    ↓
[SpecGenerator] → Creates Markdown + OpenAPI 3.0
    ↓
Output (Docs + Spec)
```

### Workflow

1. **Parse HAR**: Extract all HTTP transactions from network log
2. **Filter Noise**: Remove static assets (favicon, CSS, JS, images)
3. **Group Endpoints**: Detect patterns (`/users/123` → `/users/{id}`)
4. **Infer Types**: Analyze response JSON to deduce schemas
5. **Analyze** (optional): Use LLM to infer purpose, parameters, auth requirements
6. **Generate**: Create human-readable docs and machine-readable OpenAPI spec

## Output Examples

### Generated Markdown

```markdown
## Products

**Pattern:** `/products`

**Purpose:** Manage products resources

### Methods

- **GET**: Retrieve products

### Query Parameters

- `limit`: Unknown type

### Response

- **Type:** JSON
- **Status Codes:** 200
- **Authentication:** unknown
```

### Generated OpenAPI

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "API",
    "version": "1.0.0",
    "description": "Generated from HTTP traffic analysis"
  },
  "paths": {
    "/products": {
      "get": {
        "summary": "Retrieve products",
        "tags": ["Products"],
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "schema": {"type": "string"}
          }
        ],
        "responses": {
          "200": {
            "description": "List of products with metadata"
          }
        }
      }
    }
  }
}
```

## Supported Input Formats

- **HAR Files** (.har): Standard HTTP Archive format from browser DevTools
- **Browser Exports**: Chrome, Firefox, Edge, Safari DevTools
- **Proxy Captures**: Charles, Fiddler, Burp Suite (exported as HAR)

## Use Cases

### 1. Legacy API Documentation
- Backend exists, docs lost or outdated
- Run tool to regenerate specs from live traffic

### 2. Reverse Engineering
- Understand undocumented third-party APIs
- Detect shadow endpoints and security issues

### 3. Client SDK Generation
- Generate OpenAPI spec → auto-generate SDKs (Go, Python, TS, etc.)
- Feed spec to `openapi-generator` for production SDKs

### 4. Mock Server Setup
- Use generated OpenAPI with Prism/Mockoon
- Frontend development without waiting for backend

### 5. API Auditing
- Detect data leaks and unauthorized endpoints
- Verify compliance with expected API surface

## Roadmap

- [ ] Web UI for drag-drop HAR upload and live visualization
- [ ] Multi-format export (GraphQL schema, AsyncAPI for webhooks)
- [ ] Automated parameter type detection (string, number, boolean, enum)
- [ ] Request body schema inference
- [ ] Rate limit and authentication detection
- [ ] API versioning and changelog generation
- [ ] SQLite/PostgreSQL backend schema inference
- [ ] CLI plugin system for custom analyzers
- [ ] PyPI package publishing

## Contributing

Contributions welcome! Fork, create branch, make changes, submit PR.

**Development setup:**

```bash
git clone https://github.com/yandariss/api-behavior-learner.git
cd api-behavior-learner
pip install -r requirements.txt
pip install pytest pytest-cov black ruff
```

**Run tests:**

```bash
pytest tests/
```

**Code style:**

```bash
black api_behavior_learner/
ruff check api_behavior_learner/
```

## License

MIT License. See LICENSE file.

## Support

- Issues: https://github.com/yandariss/api-behavior-learner/issues
- Discussions: https://github.com/yandariss/api-behavior-learner/discussions

## Author

Built as a personal project exploring reverse engineering and AI-assisted API analysis.

# Getting Started with AIPentester

## What Has Been Built

This project provides a **complete foundation** for a production-quality security assessment orchestration framework. Here's what's included:

### ✅ Complete Components

1. **Project Structure** - Clean architecture with modular design
2. **Data Models** - Pydantic models for all core entities
3. **Safety Controls** - Scope validation, rate limiting, audit logging, secrets masking
4. **Storage Layer** - DuckDB adapter with complete schema
5. **CLI Framework** - Typer-based commands with Rich output
6. **Configuration** - Engagement manifest system
7. **Documentation** - README, ARCHITECTURE, THREAT_MODEL
8. **Testing** - Test suite with fixtures and mocks
9. **Development Tools** - Makefile, pre-commit hooks, linting, type checking

### 🚧 Stub Components (Ready for Implementation)

The following modules have protocol definitions and stubs ready for implementation:

1. **Browser Adapter** - Protocol defined, needs Browser Use integration
2. **Burp Adapter** - Protocol defined, needs MCP client implementation
3. **Context Ingestion** - Architecture defined, needs parser/chunker
4. **Sub-Agents** - Framework ready, needs LLM integration
5. **Review Queue** - Models defined, needs interactive UI
6. **Evidence Collection** - Models defined, needs file handling
7. **Reporting** - Templates structure ready, needs generators

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the project
cd AIPentester
make dev-install
```

### 2. Initialize a Project

```bash
aipentester init
```

This creates:
- `engagement_manifest.yaml` - Configure your authorized scope
- `.env` - Set API keys and credentials
- Project directories for evidence, audit logs, reports

### 3. Configure Your Engagement

Edit `engagement_manifest.yaml`:

```yaml
engagement:
  name: "My Assessment"
  authorized_by: "CISO Name"
  start_date: "2024-03-01"
  end_date: "2024-03-31"
  # IMPORTANT: Add authorization acknowledgement
  authorization_acknowledgement: |
    I confirm I have written authorization...

scope:
  hosts:
    - "myapp.example.com"
  excluded_paths:
    - "/admin/critical"
  max_request_rate: 5
```

### 4. Validate Configuration

```bash
aipentester validate-scope
```

This checks:
- ✅ Manifest is valid
- ✅ Engagement dates are active
- ✅ Authorization is confirmed
- ✅ Scope is properly defined
- ✅ Safety controls are enabled

### 5. Test the Setup

```bash
# Run tests
make test

# Check code quality
make lint
make type-check
```

## Next Steps: Implementing Missing Features

The architecture is complete, and the hard design decisions are made. Here's how to implement the remaining features:

### Implementing Browser Automation

File: `src/aipentester/browser/adapter.py`

```python
from browser_use import Browser

class BrowserUseAdapter:
    async def initialize(self):
        self.browser = await Browser.start()

    async def login(self, username, password, totp_secret=None):
        # Use Browser Use to automate login
        # Handle MFA if totp_secret provided
        pass
```

Resources:
- Browser Use docs: https://github.com/browser-use/browser-use
- Playwright docs: https://playwright.dev/python

### Implementing Burp Integration

File: `src/aipentester/burp/mcp_client.py`

```python
from mcp import Client

class BurpMCPClient:
    async def connect(self):
        self.client = Client(
            host=self.config.burp_mcp_host,
            port=self.config.burp_mcp_port,
        )
```

Resources:
- MCP spec: https://github.com/anthropics/mcp
- Burp Suite API docs

### Implementing Context Analysis

File: `src/aipentester/subagents/feature_extraction.py`

```python
import anthropic

class FeatureExtractionAgent:
    async def analyze(self, chunks):
        client = anthropic.Anthropic()
        # Send chunks to Claude with specialized prompt
        # Extract features, roles, workflows
        pass
```

### Implementing Review Queue

File: `src/aipentester/review_queue/interactive.py`

```python
from rich.prompt import Prompt

def present_review_item(item):
    console.print(Panel(f"""
    Action: {item.title}
    Risk: {item.risk_level}
    Target: {item.target_url}
    """))

    choice = Prompt.ask(
        "Decision",
        choices=["approve", "reject", "skip"],
    )
    return choice
```

## Architecture Decisions Made

All major design decisions have been made for you:

1. **Safety First**: Every network operation validates scope
2. **Protocol-Based**: Adapters use protocols for swappability
3. **Async Where It Matters**: Network I/O is async
4. **Pydantic Everything**: Type-safe models with validation
5. **DuckDB for Storage**: Single-file, no external DB needed
6. **Structured Logging**: JSONL audit trail
7. **Rich CLI**: Terminal UI with colors and tables
8. **Clean Architecture**: Clear separation of concerns

## File Organization

```
src/aipentester/
├── models/          # ✅ Complete - Data structures
├── safety/          # ✅ Complete - Security controls
├── storage/         # ✅ Complete - DuckDB persistence
├── cli/             # ✅ Complete - Command structure
├── browser/         # 🚧 Stub - Add Browser Use
├── burp/            # 🚧 Stub - Add MCP client
├── context_ingestion/ # 🚧 Stub - Add parser
├── subagents/       # 🚧 Stub - Add LLM calls
├── review_queue/    # 🚧 Stub - Add UI
├── evidence/        # 🚧 Stub - Add file handling
└── reporting/       # 🚧 Stub - Add generators
```

## Development Workflow

```bash
# Make changes
vim src/aipentester/browser/adapter.py

# Run tests
make test

# Check types
make type-check

# Format code
make format

# Run all checks (pre-commit)
make pre-commit
```

## Testing Strategy

All safety-critical components have tests:

- ✅ `test_safety.py` - Scope validation, secrets masking, rate limiting
- ✅ `test_models.py` - Data model validation
- 🚧 `test_browser_adapter.py` - Add when implementing browser
- 🚧 `test_burp_adapter.py` - Add when implementing Burp

## Key Files to Understand

1. **`models/engagement.py`** - Manifest schema and validation
2. **`safety/scope_validator.py`** - How scope enforcement works
3. **`safety/audit_log.py`** - Audit logging implementation
4. **`storage/duckdb_adapter.py`** - Database schema
5. **`cli/commands/validate_scope.py`** - Example complete command

## Configuration Files

- **`pyproject.toml`** - Python project config, dependencies
- **`ruff.toml`** - Linter configuration
- **`mypy.ini`** - Type checker configuration
- **`.pre-commit-config.yaml`** - Git hooks
- **`Makefile`** - Development commands

## Documentation

- **`README.md`** - User-facing documentation
- **`ARCHITECTURE.md`** - System design and data flow
- **`THREAT_MODEL.md`** - Security analysis and mitigations
- **`GETTING_STARTED.md`** (this file) - Developer guide

## Example Workflows

### Generic Assessment Mode

```bash
aipentester init
aipentester validate-scope
aipentester login
aipentester crawl --entry-point https://app.example.com
aipentester plan --mode generic
aipentester review-queue <run-id>
aipentester report <run-id>
```

### Context-Driven Mode

```bash
aipentester init
aipentester ingest-context context/*.md
aipentester plan --mode context
aipentester review-queue <run-id>
aipentester report <run-id>
```

## Safety Guarantees

This framework enforces:

1. ✅ **Scope validation** - Every URL checked before request
2. ✅ **Rate limiting** - Prevents DoS
3. ✅ **Secrets masking** - Never logs passwords/tokens
4. ✅ **Audit trail** - Every action logged
5. ✅ **Approval gates** - High-risk actions require confirmation
6. ✅ **Manifest required** - Cannot run without authorization

## Contributing

The codebase follows these principles:

- **Type hints everywhere** - Use mypy strict mode
- **Pydantic for validation** - No runtime type errors
- **Protocol-based design** - Easy to swap implementations
- **Test coverage** - Especially for safety controls
- **Documentation** - Docstrings and comments

## Common Tasks

### Add a New Command

1. Create file in `cli/commands/my_command.py`
2. Define function with Typer annotations
3. Register in `cli/main.py`
4. Add tests

### Add a New Model

1. Create Pydantic model in `models/`
2. Add database schema in `storage/duckdb_adapter.py`
3. Add tests for validation

### Add a New Sub-Agent

1. Create in `subagents/my_agent.py`
2. Implement protocol from `subagents/base.py`
3. Register in coordinator
4. Add deduplication logic

## Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
uv pip install -e ".[dev]"
```

### Type Errors

```bash
# Run mypy to see what's wrong
make type-check
```

### Tests Failing

```bash
# Run tests with verbose output
pytest -vv

# Run specific test
pytest tests/unit/test_safety.py::TestScopeValidator::test_in_scope_exact_match
```

## Resources

- **Typer**: https://typer.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Rich**: https://rich.readthedocs.io/
- **DuckDB**: https://duckdb.org/docs/
- **uv**: https://github.com/astral-sh/uv

## Support

This is a scaffolded project. Implementation details for Browser Use, Burp MCP, and LLM integration depend on your specific requirements and the current state of those libraries.

Refer to:
- `ARCHITECTURE.md` for design details
- `THREAT_MODEL.md` for security considerations
- Inline TODOs in stub files for implementation hints

## License

[Choose appropriate license - MIT, Apache 2.0, GPL, etc.]

---

**Remember**: This tool is for AUTHORIZED security testing only. Always obtain written permission before use.

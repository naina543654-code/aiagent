# AIPentester Quick Reference

## Installation

```bash
# Clone and setup
git clone <repo>
cd AIPentester
./setup.sh

# Or manual installation
uv pip install -e ".[dev]"
playwright install chromium
pre-commit install
```

## Common Commands

```bash
# Initialize new project
aipentester init

# Validate engagement manifest
aipentester validate-scope

# Show version
aipentester version

# Run tests
make test

# Code quality
make lint
make type-check
make format
```

## Project Structure Quick Look

```
src/aipentester/
├── models/          ✅ All data structures
├── safety/          ✅ Security controls
├── storage/         ✅ DuckDB persistence
├── cli/             ✅ Command framework (2/11 complete)
├── browser/         🚧 Browser Use integration
├── burp/            🚧 Burp MCP integration
├── context_ingestion/ 🚧 Context analysis
├── subagents/       🚧 LLM sub-agents
├── review_queue/    🚧 Approval UI
├── evidence/        🚧 Evidence handling
└── reporting/       🚧 Report generation
```

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `models/engagement.py` | Manifest schema | ✅ Complete |
| `safety/scope_validator.py` | Scope enforcement | ✅ Complete |
| `storage/duckdb_adapter.py` | Database | ✅ Complete |
| `cli/commands/init.py` | Project init | ✅ Complete |
| `cli/commands/validate_scope.py` | Scope check | ✅ Complete |

## Engagement Manifest (Minimal)

```yaml
engagement:
  name: "Assessment Name"
  id: "ENG-YYYY-NNN"
  authorized_by: "CISO Name"
  analyst_name: "Your Name"
  analyst_email: "you@example.com"
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  authorization_acknowledgement: "I confirm authorization..."

scope:
  hosts:
    - "app.example.com"
  max_request_rate: 5

credentials:
  source: "env"
  env_vars:
    username: "TEST_USER"
    password: "TEST_PASS"

approved_categories:
  - "xss"
  - "sqli"
  - "authz"
```

## Environment Variables (.env)

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
TEST_APP_USERNAME=testuser
TEST_APP_PASSWORD=testpass
BURP_MCP_HOST=localhost
BURP_MCP_PORT=3000
```

## Safety Controls Checklist

- ✅ Scope validation before every request
- ✅ Rate limiting enforced
- ✅ Secrets masked in all output
- ✅ Audit logging enabled
- ✅ Approval gates for high-risk actions
- ✅ Engagement manifest required
- ✅ Authorization acknowledgement mandatory

## Development Workflow

```bash
# 1. Make changes
vim src/aipentester/browser/adapter.py

# 2. Run tests
make test

# 3. Check types
make type-check

# 4. Format
make format

# 5. Run all checks
make pre-commit

# 6. Commit
git add .
git commit -m "Implement browser adapter"
```

## Testing

```bash
# All tests
pytest

# Specific module
pytest tests/unit/test_safety.py

# With coverage
pytest --cov=aipentester

# Verbose
pytest -vv
```

## Implementation Priority

1. **Browser adapter** (2-3 days) - Core functionality
2. **Evidence collector** (2-3 days) - Screenshot/request capture
3. **Review queue UI** (1-2 days) - Interactive approval
4. **Burp adapter** (2-3 days) - Burp integration
5. **Context ingestion** (3-4 days) - Document analysis
6. **Sub-agents** (4-5 days) - LLM analysis
7. **Reporting** (2-3 days) - Report generation

## Common Patterns

### Adding a New Command

```python
# src/aipentester/cli/commands/my_command.py
import typer
from rich.console import Console

console = Console()

def my_command(
    arg: str = typer.Argument(...),
    opt: str = typer.Option("default", "--option", "-o"),
) -> None:
    """Command description."""
    console.print(f"Executing with {arg} and {opt}")

# Register in cli/main.py
app.command(name="my-command")(my_command.my_command)
```

### Adding a New Model

```python
# src/aipentester/models/my_model.py
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    """Model description."""
    field: str = Field(..., description="Field description")
    optional: int = Field(default=0, ge=0)
```

### Using Safety Controls

```python
from aipentester.safety import ScopeValidator, RateLimiter
from aipentester.models import EngagementManifest

# Load manifest
manifest = EngagementManifest.from_yaml_file("engagement_manifest.yaml")

# Validate scope
validator = ScopeValidator(manifest)
validator.validate_url("https://app.example.com/test")  # Raises if out of scope

# Rate limiting
limiter = RateLimiter(max_rate=manifest.scope.max_request_rate)
await limiter.acquire()  # Waits if necessary
```

### Using Storage

```python
from aipentester.storage import DuckDBAdapter

storage = DuckDBAdapter("./aipentester.duckdb")
await storage.initialize()

# Save evidence
await storage.save_evidence({
    "run_id": "run-123",
    "type": "screenshot",
    "title": "Login page",
    # ... more fields
})

# Query evidence
evidence_list = await storage.list_evidence("run-123")
```

## Documentation

- **README.md**: User guide, installation, features
- **ARCHITECTURE.md**: System design, data flows
- **THREAT_MODEL.md**: Security analysis
- **GETTING_STARTED.md**: Developer onboarding
- **PROJECT_SUMMARY.md**: Project overview
- **QUICK_REFERENCE.md**: This file

## Troubleshooting

### "Module not found"
```bash
uv pip install -e ".[dev]"
```

### "Type errors"
```bash
make type-check  # See what's wrong
```

### "Tests failing"
```bash
pytest -vv  # Verbose output
pytest --pdb  # Drop into debugger on failure
```

### "Import errors in IDE"
- Restart IDE
- Select correct Python interpreter
- Rebuild project index

## URLs and Resources

- **Typer**: https://typer.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Rich**: https://rich.readthedocs.io/
- **DuckDB**: https://duckdb.org/docs/
- **pytest**: https://docs.pytest.org/
- **Browser Use**: https://github.com/browser-use/browser-use
- **MCP**: https://github.com/anthropics/mcp

## Support

- **Issues**: Create GitHub issue
- **Docs**: See documentation files
- **Code**: Well-commented, type-hinted

---

**Remember**: This tool is for AUTHORIZED security testing only!

# AIPentester Architecture

## Overview

AIPentester follows clean architecture principles with clear separation of concerns and protocol-based interfaces for swappable implementations.

## System Layers

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer                           │
│  Entry point, command parsing, user interaction         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Core Business Logic                     │
│  Planners, Coordinators, Workflow Managers              │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Safety Layer                            │
│  Scope Validation, Rate Limiting, Audit Logging         │
└─────┬──────────┬──────────┬─────────────┬──────────────┘
      │          │          │             │
┌─────▼──┐  ┌───▼───┐  ┌───▼────┐  ┌────▼─────┐
│Browser │  │ Burp  │  │Context │  │ Review   │
│Adapter │  │Adapter│  │Agents  │  │ Queue    │
└─────┬──┘  └───┬───┘  └───┬────┘  └────┬─────┘
      │         │          │             │
      └─────────┴──────────┴─────────────┘
                       │
              ┌────────▼──────────┐
              │  Storage Layer    │
              │  (DuckDB/SQLite)  │
              └───────────────────┘
```

## Module Breakdown

### 1. CLI Layer (`cli/`)

**Purpose**: User interface and command routing

**Components**:
- `main.py`: Typer app and command registration
- `commands/`: Individual command implementations

**Responsibilities**:
- Parse command-line arguments
- Load configuration and manifests
- Initialize components
- Display Rich-formatted output
- Handle keyboard interrupts (panic stop)

### 2. Models (`models/`)

**Purpose**: Type-safe data structures

**Components**:
- `engagement.py`: Manifest, scope, credentials
- `evidence.py`: Evidence items, findings, screenshots
- `review.py`: Review queue items, approval states
- `workflow.py`: Workflows, business logic scenarios
- `context.py`: Context chunks, sub-agent tasks

**Design**:
- All models use Pydantic for validation
- Immutable where possible
- Rich domain logic in model methods
- JSON serialization support

### 3. Safety Layer (`safety/`)

**Purpose**: Enforce security constraints

**Components**:
- `scope_validator.py`: URL/host validation against manifest
- `rate_limiter.py`: Token bucket rate limiting
- `audit_log.py`: Structured audit logging (JSONL)
- `secrets_manager.py`: Credential storage and masking

**Key Features**:
- All network operations must pass scope validation
- Rate limits enforced per-host
- All actions logged with timestamps
- Secrets masked in all outputs

**Validation Flow**:
```
Request → ScopeValidator.validate_url() → Pass/Fail
   │
   ├─ Pass → RateLimiter.acquire() → Proceed
   └─ Fail → ScopeViolationError → Halt + Log
```

### 4. Browser Adapter (`browser/`)

**Purpose**: Browser automation abstraction

**Protocol**: `BrowserAdapter`

**Key Methods**:
- `initialize()`: Start browser instance
- `login()`: Authenticate with MFA support
- `navigate()`: Go to URL (with scope check)
- `screenshot()`: Capture evidence
- `find_forms()`: Extract form metadata
- `extract_links()`: Get all page links

**Implementation** (planned):
- Use Browser Use library
- Playwright as underlying automation
- Session state persistence
- Evidence auto-capture on interesting events

### 5. Burp Adapter (`burp/`)

**Purpose**: Burp Suite integration

**Protocol**: `BurpAdapter`

**Key Methods**:
- `connect()`: Connect to MCP server
- `sync_scope()`: Push scope to Burp
- `send_to_repeater()`: Queue for manual testing
- `send_to_intruder()`: Configure attack
- `get_collaborator_address()`: Out-of-band testing
- `add_note()`: Annotate requests

**Design**:
- Uses MCP (Model Context Protocol)
- No active scanning - manual review only
- Requests tagged with evidence IDs
- Notes link back to AIPentester runs

### 6. Context Ingestion (`context_ingestion/`)

**Purpose**: Process large documentation files

**Components**:
- `parser.py`: Load and parse various formats
- `chunker.py`: Intelligent document chunking
- `coordinator.py`: Orchestrate sub-agents

**Flow**:
```
Context File → Parser → Chunker → Sub-Agents → Coordinator → Analysis
```

**Chunking Strategy**:
- Semantic chunking (preserve sections)
- Overlap for context continuity
- Token counting (stay under LLM limits)
- Metadata preservation

### 7. Sub-Agents (`subagents/`)

**Purpose**: Specialized LLM analysis agents

**Base Protocol**: `SubAgent`

**Implementations**:
- `feature_extraction.py`: Identify app features
- `authz_analysis.py`: Extract roles/permissions
- `workflow_analysis.py`: Map state transitions
- `finance_abuse.py`: Find financial flow risks
- `tenant_isolation.py`: Multi-tenancy boundary analysis
- `deduplication.py`: Merge overlapping findings

**Agent Interface**:
```python
class SubAgent(Protocol):
    async def analyze(self, chunks: list[ContextChunk]) -> SubAgentResult:
        ...
```

**Design**:
- Each agent has a specialized prompt
- Results include confidence scores
- Token usage and cost tracked
- Cacheable for incremental processing

### 8. Planner (`planner/`)

**Purpose**: Generate assessment plans

**Components**:
- `generic_planner.py`: Standard category-based plans
- `context_planner.py`: Business logic scenarios

**Output**:
- Prioritized task lists
- Evidence requirements
- Expected review tasks
- Suggested workflows

### 9. Review Queue (`review_queue/`)

**Purpose**: Human approval gates

**Components**:
- `queue.py`: Queue data structure
- `approval_gate.py`: Decision logic
- `interactive.py`: CLI prompts

**Flow**:
```
Proposed Action → Risk Assessment → Queue
   │
   └─ High Risk → Interactive Prompt → Approve/Reject
   └─ Low Risk  → Auto-proceed (if configured)
```

**Decision Factors**:
- Risk level (safe, low, medium, high, critical)
- Action type
- Manifest approval gate setting
- Historical analyst decisions

### 10. Evidence Collection (`evidence/`)

**Purpose**: Capture and store assessment artifacts

**Components**:
- `collector.py`: Gather evidence from various sources
- `encryption.py`: Encrypt sensitive evidence
- `export.py`: Package for external use

**Evidence Types**:
- Screenshots (PNG)
- HTTP requests/responses (JSON)
- Browser logs (JSON)
- Navigation trails (JSON)
- Analyst notes (Markdown)

**Encryption**:
- AES-256-GCM for files
- Key derivation from engagement ID
- Optional keyring integration

### 11. Reporting (`reporting/`)

**Purpose**: Generate assessment reports

**Components**:
- `generator.py`: Report builder
- `templates/`: Jinja2 templates

**Formats**:
- Markdown (analyst-friendly)
- JSON (machine-readable)
- HTML (stakeholder reports)

**Report Sections**:
- Executive summary
- Assessment methodology
- Scope details
- Findings with evidence
- Business logic scenarios
- Recommendations
- Evidence index

### 12. Storage (`storage/`)

**Purpose**: Persist run data

**Protocol**: `StorageAdapter`

**Implementation**: DuckDB

**Schema**:
```
runs
├─ evidence (1:N)
├─ findings (1:N)
├─ review_items (1:N)
├─ workflows (1:N)
└─ context_analysis (1:1)
```

**Design**:
- Single file per project
- JSON columns for flexibility
- Efficient queries for reporting
- No external dependencies

## Data Flow: Complete Run

```
1. aipentester init
   └─ Create project structure

2. aipentester validate-scope
   └─ Load manifest
   └─ Run ScopeValidator pre-flight checks

3. aipentester login
   └─ BrowserAdapter.login()
   └─ Save session state (encrypted)

4. aipentester crawl
   └─ BrowserAdapter.navigate()
   └─ Extract links, forms, workflows
   └─ Capture screenshots
   └─ Save evidence to EvidenceCollector

5. aipentester ingest-context
   └─ Parse context files
   └─ Chunk intelligently
   └─ Dispatch to sub-agents
   └─ Coordinator merges results
   └─ Generate business logic scenarios

6. aipentester plan
   └─ Load manifest + context analysis
   └─ GenericPlanner OR ContextPlanner
   └─ Generate assessment plan
   └─ Populate initial review queue

7. aipentester review-queue
   └─ Load ReviewQueue
   └─ Present items interactively
   └─ Analyst approves/rejects
   └─ Approved items execute
   └─ Capture results as evidence

8. aipentester burp-check
   └─ BurpAdapter.connect()
   └─ BurpAdapter.sync_scope()
   └─ Verify connectivity

9. aipentester evidence
   └─ Query storage for run evidence
   └─ Export to directory
   └─ Generate evidence index

10. aipentester report
    └─ Query storage for findings
    └─ Load evidence
    └─ Render via templates
    └─ Output report files
```

## Extension Points

### Adding a New Adapter

1. Define protocol in `<module>/protocol.py`
2. Implement concrete class
3. Register in config/settings
4. Add tests with mocks

### Adding a New Sub-Agent

1. Inherit from `SubAgent` protocol
2. Define specialized prompt
3. Implement `analyze()` method
4. Register in coordinator
5. Add deduplication logic

### Adding a New Test Category

1. Update manifest schema
2. Add to approved categories
3. Create planner templates
4. Define expected evidence types

### Adding a New Report Format

1. Create Jinja2 template
2. Add format to Reporting config
3. Implement renderer in generator.py

## Security Considerations

### Defense in Depth

1. **Scope Validation**: Every network operation
2. **Rate Limiting**: Global + per-host
3. **Approval Gates**: Intrusive actions
4. **Audit Logging**: All operations
5. **Secrets Masking**: Logs and output
6. **Encryption**: Evidence at rest

### Threat Mitigations

| Threat | Mitigation |
|--------|------------|
| Out-of-scope testing | ScopeValidator before all requests |
| Excessive impact | Rate limiting + approval gates |
| Credential leakage | SecretsManager masks all output |
| Unauthorized use | Manifest validation |
| Evidence tampering | Append-only audit log |
| Cost overruns | Token limits on sub-agents |

## Performance Considerations

- **Async I/O**: All network operations async
- **Parallel Sub-Agents**: Context analysis runs concurrently
- **Connection Pooling**: Browser sessions reused
- **Incremental Processing**: Large context files chunked
- **Caching**: LLM responses cached when appropriate

## Testing Strategy

### Unit Tests
- All safety validators
- Model validation logic
- Chunking algorithms
- Evidence collection

### Integration Tests
- End-to-end command flows
- Adapter interactions
- Storage persistence
- Report generation

### Mocks
- Browser automation mock
- Burp MCP mock
- LLM API mock

## Future Enhancements

- [ ] Plugin system for custom sub-agents
- [ ] Distributed sub-agent processing
- [ ] Real-time collaboration (multiple analysts)
- [ ] Integration with ticketing systems
- [ ] Custom report templates via config
- [ ] Passive traffic analysis mode
- [ ] GraphQL support
- [ ] WebSocket monitoring

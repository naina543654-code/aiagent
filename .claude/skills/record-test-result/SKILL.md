---
name: record-test-result
description: Record a completed test result with context and evidence in the shared findings store.
---

# Record a test result

For each completed test, capture:

- endpoint origin, path, method
- parameter and location, if applicable
- test class and methodology version
- account alias, role, and session context
- status: not_tested, inconclusive, suspected, confirmed, not_vulnerable,
  blocked, not_applicable
- concise rationale
- evidence reference and redaction status

Record it with the scope-checked write path:

```bash
aipentester findings add --title "..." --url "https://..." \
  --category xss --severity Medium --parameter q \
  --agent xss-agent --evidence "evidence/..." --evidence "request ref"
```

This records the finding as a **candidate**. The store refuses out-of-scope
URLs at write time. Then append a journal event and write the full result
to `state/inbox/<agent>-<task-id>.md`.

Before creating a new test record, check whether an equivalent record
exists for the same endpoint, parameter, test class, role/account, session
context, and methodology version (`aipentester findings list`).

Do not mark a test as not_vulnerable if it was blocked, inconclusive, or
never executed. Do not mark anything `confirmed` — only `validation-agent`
confirms, and only with attached evidence. Never record secrets, tokens,
cookies, or credentials in a finding, the journal, or evidence references.

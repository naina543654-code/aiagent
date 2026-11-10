# AIPentester Threat Model

## Purpose

This document identifies threats to the AIPentester tool itself and the mitigations in place. The goal is to ensure the tool cannot be used (even accidentally) in ways that violate ethical boundaries or cause unintended harm.

## Trust Boundaries

```
┌────────────────────────────────────────────────┐
│         Analyst (Trusted)                      │
│  - Provides manifest                           │
│  - Makes approval decisions                    │
│  - Has authorization to test targets           │
└───────────────┬────────────────────────────────┘
                │
                │ Configuration
                │
┌───────────────▼────────────────────────────────┐
│         AIPentester (Tool)                     │
│  Trust Boundary: Enforces safety controls      │
└───────────────┬────────────────────────────────┘
                │
                │ Validated Requests
                │
┌───────────────▼────────────────────────────────┐
│         Target Application (Untrusted)         │
│  - May be hostile                              │
│  - May attempt to exploit the tool             │
│  - May contain sensitive data                  │
└────────────────────────────────────────────────┘
```

## Threat Categories

### 1. Scope Violation Threats

**T1.1: Analyst Accidentally Tests Out-of-Scope Target**

- **Likelihood**: Medium
- **Impact**: Critical (legal/ethical violation)
- **Mitigations**:
  - ✅ `ScopeValidator` checks every URL before request
  - ✅ Manifest must explicitly list authorized hosts
  - ✅ Wildcards carefully validated (e.g., `*.example.com`)
  - ✅ Excluded paths enforced
  - ✅ Pre-flight validation in `validate-scope` command
- **Residual Risk**: Low
- **Testing**: Unit tests for scope validator, integration tests with out-of-scope URLs

**T1.2: Manifest Manipulation**

- **Likelihood**: Low
- **Impact**: Critical
- **Mitigations**:
  - ✅ Manifest requires explicit authorization acknowledgement
  - ✅ Engagement dates validated
  - ✅ Changes require re-running `validate-scope`
  - ✅ Audit log records manifest hash at run start
- **Residual Risk**: Low (relies on analyst integrity)

**T1.3: Scope Bypass via Redirects**

- **Likelihood**: Medium
- **Impact**: High
- **Mitigations**:
  - ✅ All redirects re-validated against scope
  - ✅ Browser adapter validates final URL
  - ✅ Redirects logged in audit trail
- **Residual Risk**: Low

### 2. Credential and Secrets Threats

**T2.1: Credentials Logged in Plaintext**

- **Likelihood**: High (without mitigation)
- **Impact**: High
- **Mitigations**:
  - ✅ `SecretsManager` masks all sensitive patterns
  - ✅ Passwords, tokens, API keys redacted from logs
  - ✅ HTTP headers (Authorization, Cookie) masked
  - ✅ Unit tests verify masking
- **Residual Risk**: Low

**T2.2: Credentials Stored Insecurely**

- **Likelihood**: Medium
- **Impact**: High
- **Mitigations**:
  - ✅ Credentials retrieved from env vars or system keyring
  - ✅ Session state encrypted at rest (AES-256-GCM)
  - ✅ Evidence can be encrypted
  - ✅ `.env` in `.gitignore`
- **Residual Risk**: Low

**T2.3: Credentials in Command History**

- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigations**:
  - ✅ No credentials accepted as CLI arguments
  - ✅ Use env vars or interactive prompts only
  - ✅ Documentation warns against command-line credentials
- **Residual Risk**: Medium (analyst must follow guidance)

### 3. Excessive Impact Threats

**T3.1: Denial of Service via Excessive Requests**

- **Likelihood**: Medium
- **Impact**: High
- **Mitigations**:
  - ✅ Rate limiter enforces max requests/second
  - ✅ Courtesy delay between requests
  - ✅ Per-host rate limiting
  - ✅ Manifest specifies max_request_rate
- **Residual Risk**: Low

**T3.2: Unintended Destructive Actions**

- **Likelihood**: Low
- **Impact**: Critical
- **Mitigations**:
  - ✅ Approval gates for intrusive actions
  - ✅ No destructive operations implemented by default
  - ✅ Review queue requires analyst approval
  - ✅ Dry-run mode available
- **Residual Risk**: Very Low

**T3.3: Runaway LLM Costs**

- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigations**:
  - ✅ `max_cost_usd` in manifest
  - ✅ Token limits per sub-agent
  - ✅ Costs tracked and reported
  - ✅ Processing stops when limit reached
- **Residual Risk**: Low

### 4. Audit and Accountability Threats

**T4.1: Audit Log Tampering**

- **Likelihood**: Low
- **Impact**: High
- **Mitigations**:
  - ✅ Append-only JSONL format
  - ✅ Timestamps on every entry
  - ✅ Log file path configurable (can use restricted permissions)
  - Future: HMAC signatures on log entries
- **Residual Risk**: Medium

**T4.2: Missing Audit Entries**

- **Likelihood**: Low
- **Impact**: Medium
- **Mitigations**:
  - ✅ All safety-critical operations logged
  - ✅ Errors logged
  - ✅ Approval decisions logged
- **Residual Risk**: Low

**T4.3: Analyst Attribution**

- **Likelihood**: Low
- **Impact**: Medium
- **Mitigations**:
  - ✅ Analyst name in manifest
  - ✅ All approvals attributed to analyst
  - ✅ Audit log includes analyst identity
- **Residual Risk**: Low

### 5. Tool Compromise Threats

**T5.1: Malicious Context File**

- **Likelihood**: Low
- **Impact**: Medium
- **Mitigations**:
  - ✅ Context parser handles errors gracefully
  - ✅ No code execution from context files
  - ✅ Token limits prevent resource exhaustion
  - ✅ LLM prompts sanitized
- **Residual Risk**: Low

**T5.2: Malicious Target Response**

- **Likelihood**: Medium
- **Impact**: Low
- **Mitigations**:
  - ✅ Playwright sandboxing
  - ✅ No eval() or code execution from responses
  - ✅ Evidence files stored with safe naming
- **Residual Risk**: Low

**T5.3: Dependency Vulnerabilities**

- **Likelihood**: Medium
- **Impact**: Varies
- **Mitigations**:
  - ✅ Use `uv` for dependency management
  - ✅ Pin dependencies
  - Future: Dependabot alerts
  - Future: Regular security audits
- **Residual Risk**: Medium

### 6. Misuse Threats

**T6.1: Unauthorized Use**

- **Likelihood**: Medium (if tool is widely distributed)
- **Impact**: Critical
- **Mitigations**:
  - ✅ Engagement manifest required
  - ✅ Authorization acknowledgement required
  - ✅ Documentation emphasizes authorized use only
  - ✅ Audit logs provide evidence of misuse
  - ⚠️ Tool cannot technically prevent determined misuse
- **Residual Risk**: **High** (relies on user ethics and legal system)

**T6.2: Bypassing Safety Controls**

- **Likelihood**: Low
- **Impact**: High
- **Mitigations**:
  - ✅ Safety controls deeply integrated (not superficial)
  - ✅ Scope validation cannot be disabled
  - ✅ Audit logging always enabled
  - ✅ Approval gates configurable but logged
- **Residual Risk**: Medium (analyst could modify code)

**T6.3: Use Against Critical Infrastructure**

- **Likelihood**: Very Low
- **Impact**: Critical
- **Mitigations**:
  - ✅ Documentation explicitly warns against unauthorized testing
  - ✅ Rate limiting and courtesy delays reduce impact
  - ✅ No weaponized exploits included
  - ✅ Tool designed for assessment, not exploitation
- **Residual Risk**: **High** (relies on user responsibility)

## Attack Surface

### Inputs

| Input | Trust Level | Validation |
|-------|-------------|------------|
| Engagement manifest | Trusted (analyst) | Pydantic schema validation |
| Context files | Trusted (analyst) | Parser with error handling |
| CLI arguments | Trusted (analyst) | Typer validation |
| Environment variables | Trusted (analyst) | Masked in logs |
| Target HTTP responses | **Untrusted** | Playwright sandbox, no eval |
| LLM responses | **Untrusted** | Structured output parsing |

### Outputs

| Output | Sensitivity | Protection |
|--------|-------------|------------|
| Audit logs | High | Secrets masked |
| Evidence files | High | Optional encryption |
| Reports | High | Secrets masked |
| Database | High | Local file, can be encrypted |
| Terminal output | Medium | Secrets masked |

## Security Invariants

These properties must ALWAYS hold:

1. **Every network request is validated against scope**
2. **Secrets never appear in logs or terminal output**
3. **Every action is logged to audit trail**
4. **Intrusive actions require approval (if enabled)**
5. **Rate limits are enforced**

## Testing for Threats

### Test Cases

**Scope Validation**:
- [ ] Out-of-scope host rejected
- [ ] Out-of-scope path rejected
- [ ] Redirect to out-of-scope host rejected
- [ ] Wildcard patterns work correctly
- [ ] IP-based scope works

**Secrets Masking**:
- [ ] Password in HTTP request masked
- [ ] API key in log masked
- [ ] Authorization header masked
- [ ] Cookie header masked
- [ ] TOTP secret masked

**Rate Limiting**:
- [ ] Requests delayed to meet max_request_rate
- [ ] Courtesy delay applied
- [ ] Per-host limits enforced

**Approval Gates**:
- [ ] High-risk actions queued
- [ ] Approved actions execute
- [ ] Rejected actions skip
- [ ] Approvals logged with analyst name

**Audit Logging**:
- [ ] All requests logged
- [ ] Errors logged
- [ ] Approval decisions logged
- [ ] Scope violations logged

## Incident Response

### If Tool is Misused

1. **Audit log provides evidence of actions taken**
2. **Engagement manifest shows claimed authorization**
3. **Timestamps prove activity window**
4. **Evidence files show targets accessed**

### If Tool is Compromised

1. **Verify dependency integrity**
2. **Check audit logs for anomalies**
3. **Review recent code changes**
4. **Rotate credentials**
5. **Re-validate all evidence**

## Recommendations for Analysts

1. ✅ **Always obtain written authorization before use**
2. ✅ **Carefully review engagement manifest**
3. ✅ **Use dry-run mode to verify safety**
4. ✅ **Enable approval gates for high-risk assessments**
5. ✅ **Regularly review audit logs**
6. ✅ **Rotate credentials after engagement**
7. ✅ **Encrypt evidence for sensitive assessments**
8. ✅ **Delete evidence after retention period**
9. ✅ **Never share credentials in manifests**
10. ✅ **Run `validate-scope` before every engagement**

## Known Limitations

1. **Tool cannot verify authenticity of authorization** - relies on analyst integrity
2. **Tool cannot prevent code modification** - open source, can be forked
3. **Rate limiting is cooperative** - not enforced at network level
4. **Secrets masking is pattern-based** - novel secret formats might not be caught
5. **Audit logs are not cryptographically signed** - can be tampered by privileged user

## Future Security Enhancements

- [ ] Cryptographic signatures on audit log entries
- [ ] Integration with authorization management systems
- [ ] Hardware security module (HSM) integration for secrets
- [ ] Tamper-evident evidence packaging
- [ ] Network-level rate limiting (iptables integration)
- [ ] Anomaly detection in audit logs
- [ ] Multi-analyst approval for critical actions
- [ ] Time-based restrictions (only test during engagement window)
- [ ] Automatic evidence encryption with organization keys
- [ ] Integration with security information and event management (SIEM)

## Conclusion

AIPentester prioritizes safety through defense-in-depth:
- Multiple layers of validation
- Comprehensive audit logging
- Secrets protection
- Rate limiting
- Human approval gates

However, **the tool ultimately relies on analyst ethics and authorization**. It is a force multiplier for authorized security testing, not a safeguard against determined misuse.

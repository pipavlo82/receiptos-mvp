# Security & Trust Boundaries (MVP)

## Scope
ReceiptOS is a verification shell for signed decision receipts.
It provides integrity/replay/chain checks for agent tool-call workflows in a lightweight, demo-ready form.

This document defines what is guaranteed now, and what is explicitly out-of-scope.

---

## What ReceiptOS guarantees (MVP)
1. **Tamper evidence**
   - Post-sign payload mutation is detected (`TAMPER`).
2. **Replay policy signaling**
   - Duplicate decision identity/nonce is rejected with structured reason (`REPLAY`).
3. **Deterministic verification**
   - Same payload + trust config => stable reason-coded result.
4. **Chain integrity checks**
   - `prev_hash` continuity can be validated with fail index/reason.
5. **Machine-readable outcomes**
   - Verify/verify-chain return structured reason codes suitable for automation.

---

## What ReceiptOS does NOT guarantee (MVP)
1. Full enterprise key lifecycle management (HSM/KMS, rotation orchestration, revocation workflows)
2. Protection against compromised signer hosts before signing
3. Correctness of business policy/decision intent (integrity != business correctness)
4. Complete anti-fraud/security stack on its own

---

## Demo vs Production boundaries

### Demo-ready now
- One-command demo flow
- CLI + API verification shell
- Tamper/replay/chain mismatch visibility
- Explicit reason codes

### Required before production-grade claims
- Hardened key management and signer trust governance
- Durable storage and operational controls
- Expanded adversarial testing and runbook procedures
- Deployment hardening (authN/authZ, rate limits, abuse controls)

---

## Threat model (lite)

### In-scope now
- Payload tampering after signing
- Accidental/naive replay attempts
- Chain-link mismatch/fork indicators
- Schema/signature/trust violations surfaced as reason codes

### Partially in-scope
- Untrusted signer detection when trust list is configured

### Out-of-scope now
- Key exfiltration / compromised signer runtime
- Advanced insider misuse with authorized keys
- Distributed Byzantine consistency guarantees
- Full IAM/PAM and regulatory controls

---

## Non-goals (current phase)
- UI/dashboard productization
- Enterprise auth/tenant framework
- Distributed checkpoint orchestration
- PQC production integration
- Full compliance certification package

---

## Positioning discipline
Present ReceiptOS as:
**Verifiable execution layer for agent tool calls.**

Do not present it yet as:
- complete enterprise security suite,
- universal anti-fraud platform,
- production trust fabric with full key governance.

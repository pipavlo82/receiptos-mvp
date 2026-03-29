# ReceiptOS MVP (Day-1+)

**ReceiptOS = trust layer / verifiable execution layer for agent tool calls.**

It signs and verifies decision receipts so agent actions are auditable, tamper-evident, and replay-detectable.

---

## What problem it solves

Agent systems call tools, get outputs, then decide.
Without a trust layer, it is hard to prove:
- what tool input/output was actually used,
- why a decision was made,
- whether data was tampered post-decision,
- whether events were replayed.

ReceiptOS provides signed receipts with hash-chain support for this exact gap.

---

## Why this matters for agent/tool-call systems

For Codex/plugin-style workflows, ReceiptOS gives:
- deterministic decision provenance,
- verifiable integrity of tool_call input/output,
- append-only decision history,
- chain validation for audit/forensics.

## Who should use this now
- teams shipping tool-calling agents and needing auditable execution
- automation/risk/compliance workflows where replay/tamper matters
- builders needing a lightweight trust layer before full platform hardening

---

## Quick demo (one command)

```bash
cd /mnt/d/prop_bot
python3 receiptos_mvp/examples/demo_all.py
```

This runs full show flow and ends with PASS/FAIL summary.

## CI / Smoke

```bash
python3 -m pytest receiptos_mvp/tests/test_smoke.py receiptos_mvp/tests/test_reason_codes.py
bash receiptos_mvp/scripts/smoke.sh
```

## Handy commands (task runner)

```bash
cd /mnt/d/prop_bot/receiptos_mvp
make demo
make smoke
make test
make replay-demo
```

## API replay demo

```bash
python3 receiptos_mvp/examples/api_replay_demo.py
```
Expected second ingest: HTTP `409` and `reason_code = "REPLAY"`.

## Quickstart (manual, 60-90s)

```bash
cd /mnt/d/prop_bot

# 1) Sign sample tool-call payload
python3 -m receiptos_mvp.src.cli sign \
  --input receiptos_mvp/examples/sample_tool_payload.json \
  --output receiptos_mvp/examples/sample_receipt.json \
  --chain --append \
  --ledger receiptos_mvp/examples/decision_receipts.jsonl

# 2) Verify single receipt
python3 -m receiptos_mvp.src.cli verify \
  --input receiptos_mvp/examples/sample_receipt.json

# 3) Verify chain
python3 -m receiptos_mvp.src.cli verify-chain \
  --ledger receiptos_mvp/examples/decision_receipts.jsonl

# 4) Main Codex-style agent demo
python3 receiptos_mvp/examples/codex_agent_demo.py

# 5) Tamper demo
python3 receiptos_mvp/examples/tamper_demo.py

# 6) Replay demo
python3 receiptos_mvp/examples/replay_demo.py
```

Expected in Codex demo:
- `✔ original decision verified`
- `❌ tampered tool output detected`

---

## Core CLI commands

- `receiptos sign`
  - signs payload, writes hashes/signature, optional chain link and ledger append.
- `receiptos verify`
  - verifies payload hash + receipt hash + signature.
- `receiptos verify-chain`
  - verifies every receipt + prev_hash continuity + duplicate id/nonce checks.

---

## API endpoints (minimal shell)

Run:
```bash
python -m receiptos_mvp.src.api
```

Endpoints:
- `POST /v1/sign`
- `POST /v1/verify`
- `POST /v1/receipts`
- `POST /v1/verify-chain`

---

## Demo scripts

- `receiptos_mvp/examples/codex_agent_demo.py` **(primary demo)**
- `receiptos_mvp/examples/tamper_demo.py`
- `receiptos_mvp/examples/replay_demo.py`
- `receiptos_mvp/examples/integration_stub.py`

---

## What ReceiptOS detects

- **Tamper:** post-sign changes in decision/tool_call payload (`TAMPER`)
- **Replay:** duplicate decision_id/nonce/seq policy violations (`REPLAY`)
- **Chain mismatch:** invalid `prev_hash` links (`CHAIN_PREV_HASH_MISMATCH`)
- **Signature/auth issues:** (`BAD_SIGNATURE`, `UNTRUSTED_SIGNER`)
- **Sequence integrity:** (`SEQ_GAP`)
- **Clock anomalies (optional check):** (`CLOCK_SKEW`)
- **Schema issues:** (`INVALID_SCHEMA`)

---

## Tool-call aware schema support

Receipt schema supports:
```json
{
  "tool_call": {
    "name": "tool_name",
    "input": {"...": "..."},
    "output": {"...": "..."}
  },
  "decision": {
    "action": "...",
    "confidence": 0.0
  }
}
```

`tool_call.input` and `tool_call.output` are included in canonical payload hashing.

---

## Day-1 limits / Day-2 notes

### Day-1
- local file ledger
- HMAC-SHA256 signing baseline
- minimal API + demos

### Day-2 (next)
- key management abstraction (Ed25519/PQC options)
- receipt status codes + richer chain/fork handling
- verification service hardening + CI matrix
- optional timeline viewer

---

## Next roadmap hook

Move from MVP shell to integration-ready package:
1. stable SDK/API contract,
2. verifier CLI for CI/CD,
3. signed receipt export for compliance/audit pipelines.

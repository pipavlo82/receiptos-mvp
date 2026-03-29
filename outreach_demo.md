# ReceiptOS Outreach Demo

## 30-second pitch
ReceiptOS is a **verifiable execution layer for agent tool calls**.
It signs tool-call context + decision payloads, verifies integrity deterministically, and surfaces machine-readable reason codes for tamper/replay/chain failures.

In short: not just “what the agent logged,” but **what can be proven**.

---

## 90-second demo narrative
1. Run one command: `python3 receiptos_mvp/examples/demo_all.py`.
2. Show normal flow:
   - sign payload,
   - verify receipt (`reason_code=OK`),
   - chain verify (`OK`).
3. Show trust failure:
   - tamper tool output post-sign,
   - verify fails with `reason_code=TAMPER`.
4. Show replay defense:
   - ingest same signed receipt twice via API,
   - second request returns `HTTP 409` + `reason_code=REPLAY`.

Outcome: ReceiptOS demonstrates verifiable execution semantics, not plain observability.

---

## Copy/paste commands

```bash
cd /mnt/d/prop_bot
python3 receiptos_mvp/examples/demo_all.py
```

```bash
python3 receiptos_mvp/examples/codex_agent_demo.py
```

```bash
python3 receiptos_mvp/examples/api_replay_demo.py
```

---

## What this demo proves
- Deterministic verify outcomes (`OK`, `TAMPER`, `REPLAY`, etc.)
- Tool-call input/output are cryptographically bound into receipt integrity
- Replay policy is visible at API level (409 + reason code)
- Chain continuity checks are machine-readable and CI-friendly

---

## Who should care first
1. Agent platform teams shipping tool-enabled workflows
2. Automation teams with high-impact decisions (finance/ops/support)
3. Risk/compliance engineers needing auditable execution provenance

---

## Why this is not just logging
Logging records claims.
ReceiptOS verifies claims.

It provides signed canonical payload integrity + replay policy + chain semantics — a trust layer for agent execution.
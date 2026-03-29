# ReceiptOS MVP Runbook

## 0) One-command showable demo (primary)
```bash
cd /mnt/d/prop_bot
python3 receiptos_mvp/examples/demo_all.py
```
Expected end summary with PASS/FAIL lines for sign/verify/codex/tamper/replay/verify-chain.

## 0.1) Primary Codex-style demo only
```bash
python3 receiptos_mvp/examples/codex_agent_demo.py
```
Expected:
- `✔ original decision verified`
- `❌ tampered tool output detected`

## 1) Sign sample tool-call payload
```bash
python -m receiptos_mvp.src.cli sign \
  --input receiptos_mvp/examples/sample_tool_payload.json \
  --output receiptos_mvp/examples/sample_receipt.json \
  --chain --append \
  --ledger receiptos_mvp/examples/decision_receipts.jsonl
```

## 2) Verify single receipt
```bash
python -m receiptos_mvp.src.cli verify \
  --input receiptos_mvp/examples/sample_receipt.json
```

## 3) Verify chain
```bash
python -m receiptos_mvp.src.cli verify-chain \
  --ledger receiptos_mvp/examples/decision_receipts.jsonl
```

## 4) Tamper demo
```bash
python receiptos_mvp/examples/tamper_demo.py
```

## 5) Replay demo
```bash
python receiptos_mvp/examples/replay_demo.py
```

## 6) Integration stub
```bash
python receiptos_mvp/examples/integration_stub.py
```

## 7) API replay demo (explicit 409 + REPLAY)
```bash
python3 receiptos_mvp/examples/api_replay_demo.py
```

## 8) CI / smoke
```bash
python3 -m pytest receiptos_mvp/tests/test_smoke.py receiptos_mvp/tests/test_reason_codes.py
bash receiptos_mvp/scripts/smoke.sh
```

## 8.1) Handy commands
```bash
cd /mnt/d/prop_bot/receiptos_mvp
make demo
make smoke
make test
make replay-demo
```

## 9) Start API server
```bash
python3 -m receiptos_mvp.src.api
```
Endpoints:
- POST /v1/sign
- POST /v1/verify
- POST /v1/receipts
- POST /v1/verify-chain

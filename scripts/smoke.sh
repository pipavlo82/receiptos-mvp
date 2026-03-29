#!/usr/bin/env bash
set -euo pipefail
cd /mnt/d/prop_bot

LEDGER=receiptos_mvp/examples/smoke_ledger.jsonl
rm -f "$LEDGER"

python3 -m receiptos_mvp.src.cli sign \
  --input receiptos_mvp/examples/sample_tool_payload.json \
  --output receiptos_mvp/examples/sample_receipt.json \
  --chain --append \
  --ledger "$LEDGER" >/dev/null

python3 -m receiptos_mvp.src.cli verify \
  --input receiptos_mvp/examples/sample_receipt.json >/dev/null

python3 -m receiptos_mvp.src.cli verify-chain \
  --ledger "$LEDGER" >/dev/null

python3 receiptos_mvp/examples/codex_agent_demo.py >/dev/null
python3 receiptos_mvp/examples/tamper_demo.py >/dev/null
python3 receiptos_mvp/examples/replay_demo.py >/dev/null
python3 receiptos_mvp/examples/demo_all.py >/dev/null

echo "[PASS] receiptos_mvp smoke"

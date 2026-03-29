#!/usr/bin/env python3
from __future__ import annotations

# Minimal Codex/plugin-style integration example (local call path)
from pathlib import Path
import json, sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from receiptos import sign_receipt, verify_receipt

payload = {
    'actor': {'agent': 'external-runtime', 'policy': 'ext-policy-v1'},
    'inputs': {'context_hash': 'ext-task-123', 'source_refs': ['tool_x']},
    'tool_call': {'name': 'weather_api', 'input': {'city': 'Kyiv'}, 'output': {'temp_c': 12, 'condition': 'cloudy'}},
    'decision': {'action': 'send_weather_reply', 'confidence': 0.79},
    'evidence': [{'kind': 'tool_output', 'value': 'ok', 'weight': 0.4}],
    'nonce': 'integration-stub-1'
}

receipt = sign_receipt(payload, secret='demo-secret-change-me', key_id='stub-k1')
valid, debug = verify_receipt(receipt, secret='demo-secret-change-me')
print(json.dumps({'valid': valid, 'decision_id': receipt.get('decision_id'), 'debug': debug}, ensure_ascii=False))

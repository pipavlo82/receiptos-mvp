from __future__ import annotations
import json
from pathlib import Path
from receiptos import sign_receipt, verify_receipt, append_jsonl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'examples' / 'decision_receipts.jsonl'
SECRET = 'demo-secret-change-me'

base_payload = {
    'actor': {'agent': 'agent_decision_sandbox', 'policy': 'policy_agent_decision_sandbox.json', 'model': 'qwen2.5:3b-instruct'},
    'inputs': {'context_hash': 'ctx_abc123', 'source_refs': ['latest_verdict.json', 'trace_learning_memory.json']},
    'decision': {'action': 'adjust_exit', 'confidence': 0.71, 'size_mult': 0.9, 'note': 'churn+entropy high'},
    'evidence': [
        {'kind': 'churn_fee', 'value': 'fee_bleed', 'weight': 0.32},
        {'kind': 'entropy', 'value': 0.88, 'weight': 0.24},
        {'kind': 'trace_conflict', 'value': ['fee_bleed_cycle'], 'weight': 0.17}
    ]
}

r1 = sign_receipt(base_payload, SECRET, key_id='demo-k1', prev_hash=None)
append_jsonl(OUT, r1)

payload2 = json.loads(json.dumps(base_payload))
payload2['decision'] = {'action': 'tighten', 'confidence': 0.67, 'size_mult': 0.8, 'note': 'post-veto adjustment'}
r2 = sign_receipt(payload2, SECRET, key_id='demo-k1', prev_hash=r1['hashes']['receipt_sha256'])
append_jsonl(OUT, r2)

ok1, d1 = verify_receipt(r1, SECRET)
ok2, d2 = verify_receipt(r2, SECRET)
print({'written': str(OUT), 'verify_r1': ok1, 'verify_r2': ok2, 'r1_debug': d1, 'r2_debug': d2})

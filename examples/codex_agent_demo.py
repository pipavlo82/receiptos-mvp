#!/usr/bin/env python3
from __future__ import annotations

import json, copy, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from receiptos import sign_receipt, verify_receipt

SECRET = 'demo-secret-change-me'


def mock_pricing_api(sku: str, region: str) -> dict:
    # deterministic mock output
    price_map = {'ABC-1': 42.5, 'ABC-2': 19.0}
    return {
        'price': price_map.get(sku, 10.0),
        'currency': 'USD',
        'confidence': 0.94,
        'region': region,
    }


def main():
    # 1) agent receives user task
    user_task = {'task': 'Quote customer for SKU ABC-1 in US'}

    # 2) agent calls tool
    tool_in = {'sku': 'ABC-1', 'region': 'US'}
    tool_out = mock_pricing_api(**tool_in)

    # 3) agent decision + receipt payload
    payload = {
        'actor': {'agent': 'codex-style-agent', 'policy': 'receiptos_demo_policy_v1', 'model': 'demo-model'},
        'inputs': {'context_hash': f"task:{user_task['task']}", 'source_refs': ['user_task', 'pricing_api']},
        'tool_call': {'name': 'pricing_api', 'input': tool_in, 'output': tool_out},
        'decision': {'action': 'quote_customer', 'confidence': 0.88, 'size_mult': 1.0},
        'evidence': [
            {'kind': 'tool_output_confidence', 'value': tool_out['confidence'], 'weight': 0.5},
            {'kind': 'policy_rule', 'value': 'price_confidence>=0.9', 'weight': 0.3}
        ],
        'nonce': 'codex-demo-nonce-1',
    }

    signed = sign_receipt(payload, SECRET, key_id='demo-k1')
    ok, _ = verify_receipt(signed, SECRET)
    if ok:
        print('✔ original decision verified')
    else:
        print('❌ original decision failed unexpectedly')
        raise SystemExit(2)

    # 4) tamper tool output and verify must fail
    tampered = copy.deepcopy(signed)
    tampered['tool_call']['output']['price'] = 420.0
    ok2, dbg2 = verify_receipt(tampered, SECRET)
    if not ok2:
        print('❌ tampered tool output detected')
        print(json.dumps({'debug': dbg2}, ensure_ascii=False))
    else:
        print('⚠ tamper was not detected (unexpected)')
        raise SystemExit(2)


if __name__ == '__main__':
    main()

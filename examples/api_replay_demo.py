#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from receiptos import sign_receipt, verify_receipt, append_jsonl  # noqa

# Prefer real API test-client path; fallback to lightweight local emulation when Flask is unavailable.
try:
    from api import app, LEDGER, SEEN  # type: ignore
    HAVE_FLASK_API = True
except Exception:
    HAVE_FLASK_API = False
    app = None
    LEDGER = Path('/mnt/d/prop_bot/receiptos_mvp/examples/decision_receipts.jsonl')
    SEEN = Path('/mnt/d/prop_bot/receiptos_mvp/examples/seen_nonces.json')


def _load_seen():
    if SEEN.exists():
        try:
            return json.loads(SEEN.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            return {'decision_ids': [], 'nonces': []}
    return {'decision_ids': [], 'nonces': []}


def _save_seen(v):
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf-8')


def _local_ingest(receipt: dict):
    ok, dbg = verify_receipt(receipt, 'demo-secret-change-me')
    if not ok:
        return 422, {'accepted': False, 'reason_code': dbg.get('reason_code', 'INVALID_SCHEMA'), 'debug': dbg}
    seen = _load_seen()
    rid = receipt.get('decision_id'); nonce = receipt.get('nonce')
    if rid and rid in seen.get('decision_ids', []):
        return 409, {'accepted': False, 'reason_code': 'REPLAY', 'reason': 'duplicate_decision_id'}
    if nonce and nonce in seen.get('nonces', []):
        return 409, {'accepted': False, 'reason_code': 'REPLAY', 'reason': 'duplicate_nonce_replay'}
    append_jsonl(LEDGER, receipt)
    if rid: seen.setdefault('decision_ids', []).append(rid)
    if nonce: seen.setdefault('nonces', []).append(nonce)
    _save_seen(seen)
    return 200, {'accepted': True, 'reason_code': 'OK'}


def main():
    # clean local demo state (receiptos_mvp-only)
    if LEDGER.exists():
        LEDGER.unlink()
    if SEEN.exists():
        SEEN.unlink()

    payload = {
        'actor': {'agent': 'api-demo-agent', 'policy': 'api-demo-policy'},
        'inputs': {'context_hash': 'api-replay-demo', 'source_refs': ['demo']},
        'tool_call': {'name': 'weather_api', 'input': {'city': 'Kyiv'}, 'output': {'temp_c': 12}},
        'decision': {'action': 'send_weather_reply', 'confidence': 0.77},
        'evidence': [{'kind': 'tool_output', 'value': 'ok', 'weight': 0.4}],
        'decision_id': 'api-replay-fixed-id',
        'nonce': 'api-replay-fixed-nonce'
    }
    signed = sign_receipt(payload, secret='demo-secret-change-me', key_id='api-k1')

    if HAVE_FLASK_API:
        with app.test_client() as c:
            r1 = c.post('/v1/receipts', json=signed)
            status1, body1 = r1.status_code, (r1.get_json() or {})
            r2 = c.post('/v1/receipts', json=copy.deepcopy(signed))
            status2, body2 = r2.status_code, (r2.get_json() or {})
    else:
        status1, body1 = _local_ingest(signed)
        status2, body2 = _local_ingest(copy.deepcopy(signed))

    if status1 == 200 and body1.get('accepted') is True:
        print('✔ first ingest accepted')
    else:
        print('❌ first ingest failed unexpectedly')
        print(json.dumps({'status': status1, 'body': body1}, ensure_ascii=False))
        raise SystemExit(2)

    if status2 == 409 and body2.get('reason_code') == 'REPLAY':
        print('❌ second ingest rejected as replay')
        print(json.dumps({'status': status2, 'body': body2}, ensure_ascii=False))
    else:
        print('⚠ replay policy did not trigger as expected')
        print(json.dumps({'status': status2, 'body': body2}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == '__main__':
    main()

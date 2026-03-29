#!/usr/bin/env python3
from __future__ import annotations

from flask import Flask, request, jsonify
from pathlib import Path
import json
try:
    from .receiptos import sign_receipt, verify_receipt, append_jsonl
except Exception:
    from receiptos import sign_receipt, verify_receipt, append_jsonl

app = Flask(__name__)
SECRET = 'demo-secret-change-me'
LEDGER = Path('/mnt/d/prop_bot/receiptos_mvp/examples/decision_receipts.jsonl')
SEEN = Path('/mnt/d/prop_bot/receiptos_mvp/examples/seen_nonces.json')


def _load_seen():
    if SEEN.exists():
        try: return json.loads(SEEN.read_text(encoding='utf-8'))
        except Exception: return {'decision_ids': [], 'nonces': []}
    return {'decision_ids': [], 'nonces': []}


def _save_seen(v):
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding='utf-8')


@app.post('/v1/sign')
def sign_ep():
    payload = request.get_json(force=True, silent=True) or {}
    chain = bool(payload.pop('chain', False))
    prev = None
    if chain and LEDGER.exists():
        lines = LEDGER.read_text(encoding='utf-8', errors='ignore').splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                prev = (last.get('hashes') or {}).get('receipt_sha256')
            except Exception:
                prev = None
    out = sign_receipt(payload, SECRET, key_id='api-k1', prev_hash=prev)
    return jsonify(out)


@app.post('/v1/verify')
def verify_ep():
    receipt = request.get_json(force=True, silent=True) or {}
    trusted = request.headers.get('X-Trusted-Kids')
    trusted_kids = set(x.strip() for x in trusted.split(',') if x.strip()) if trusted else None
    max_skew = request.headers.get('X-Max-Clock-Skew-Sec')
    max_skew_i = int(max_skew) if max_skew and max_skew.isdigit() else None
    ok, dbg = verify_receipt(receipt, SECRET, trusted_kids=trusted_kids, max_clock_skew_sec=max_skew_i)
    return jsonify({'valid': ok, 'reason_code': dbg.get('reason_code'), 'debug': dbg}), (200 if ok else 422)


@app.post('/v1/receipts')
def ingest_ep():
    receipt = request.get_json(force=True, silent=True) or {}
    ok, dbg = verify_receipt(receipt, SECRET)
    if not ok:
        return jsonify({'accepted': False, 'reason_code': dbg.get('reason_code', 'INVALID_SCHEMA'), 'debug': dbg}), 422

    seen = _load_seen()
    rid = receipt.get('decision_id'); nonce = receipt.get('nonce')
    if rid and rid in seen.get('decision_ids', []):
        return jsonify({'accepted': False, 'reason_code': 'REPLAY', 'reason': 'duplicate_decision_id'}), 409
    if nonce and nonce in seen.get('nonces', []):
        return jsonify({'accepted': False, 'reason_code': 'REPLAY', 'reason': 'duplicate_nonce_replay'}), 409

    append_jsonl(LEDGER, receipt)
    if rid: seen.setdefault('decision_ids', []).append(rid)
    if nonce: seen.setdefault('nonces', []).append(nonce)
    _save_seen(seen)
    return jsonify({'accepted': True, 'reason_code': 'OK', 'index': len(LEDGER.read_text(encoding='utf-8', errors='ignore').splitlines()) - 1})


@app.post('/v1/verify-chain')
def verify_chain_ep():
    body = request.get_json(force=True, silent=True) or {}
    rows = body.get('receipts', [])
    prev = None
    seen_ids = set(); seen_nonces = set(); seq_seen = set(); expected_seq = None
    for i, r in enumerate(rows):
        ok, dbg = verify_receipt(r, SECRET)
        if not ok:
            return jsonify({'valid': False, 'reason_code': dbg.get('reason_code', 'INVALID_SCHEMA'), 'fail_index': i, 'fail_seq': r.get('seq'), 'debug': dbg}), 422

        rid = r.get('decision_id'); nonce = r.get('nonce')
        if rid and rid in seen_ids:
            return jsonify({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'reason': 'duplicate_decision_id'}), 422
        if nonce and nonce in seen_nonces:
            return jsonify({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'reason': 'duplicate_nonce_replay'}), 422
        if rid: seen_ids.add(rid)
        if nonce: seen_nonces.add(nonce)

        seq = r.get('seq')
        if seq is not None:
            try:
                seq = int(seq)
            except Exception:
                return jsonify({'valid': False, 'reason_code': 'INVALID_SCHEMA', 'fail_index': i, 'reason': 'seq_not_int'}), 422
            if seq in seq_seen:
                return jsonify({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'reason': 'duplicate_seq'}), 422
            seq_seen.add(seq)
            if expected_seq is None:
                expected_seq = seq
            elif seq != expected_seq + 1:
                return jsonify({'valid': False, 'reason_code': 'SEQ_GAP', 'fail_index': i, 'expected_seq': expected_seq + 1, 'got_seq': seq}), 422
            expected_seq = seq

        cur_prev = (r.get('hashes') or {}).get('prev_receipt_sha256')
        if i == 0:
            if cur_prev not in (None, '', 'null'):
                return jsonify({'valid': False, 'reason_code': 'CHAIN_PREV_HASH_MISMATCH', 'fail_index': i, 'reason': 'genesis_prev_hash_must_be_null'}), 422
        else:
            if cur_prev != prev:
                return jsonify({'valid': False, 'reason_code': 'CHAIN_PREV_HASH_MISMATCH', 'fail_index': i, 'expected': prev, 'got': cur_prev}), 422
        prev = (r.get('hashes') or {}).get('receipt_sha256')
    return jsonify({'valid': True, 'reason_code': 'OK', 'checked': len(rows), 'last_hash': prev})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8797)

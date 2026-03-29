#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path
try:
    from .receiptos import sign_receipt, verify_receipt, append_jsonl
except Exception:
    from receiptos import sign_receipt, verify_receipt, append_jsonl


def load_secret(v: str | None) -> str:
    if not v:
        return 'demo-secret-change-me'
    p = Path(v)
    if p.exists():
        return p.read_text(encoding='utf-8', errors='ignore').strip()
    return v


def cmd_sign(args):
    secret = load_secret(args.secret)
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    prev = None
    ledger = Path(args.ledger)
    if args.chain and ledger.exists():
        lines = ledger.read_text(encoding='utf-8', errors='ignore').splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                prev = (last.get('hashes') or {}).get('receipt_sha256')
            except Exception:
                prev = None
    signed = sign_receipt(payload, secret, key_id=args.kid, prev_hash=prev)
    out = Path(args.output) if args.output else None
    if out:
        out.write_text(json.dumps(signed, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.append:
        append_jsonl(ledger, signed)
    print(json.dumps({'ok': True, 'decision_id': signed.get('decision_id'), 'receipt_sha256': signed.get('hashes',{}).get('receipt_sha256')}))


def _load_trusted_kids(v: str | None):
    if not v:
        return None
    p = Path(v)
    if p.exists():
        try:
            arr = json.loads(p.read_text(encoding='utf-8', errors='ignore'))
            if isinstance(arr, list):
                return set(str(x) for x in arr)
        except Exception:
            pass
    return set(x.strip() for x in v.split(',') if x.strip())


def cmd_verify(args):
    secret = load_secret(args.secret)
    receipt = json.loads(Path(args.input).read_text(encoding='utf-8'))
    trusted = _load_trusted_kids(args.trusted_kids)
    ok, dbg = verify_receipt(receipt, secret, trusted_kids=trusted, max_clock_skew_sec=args.max_clock_skew_sec)
    print(json.dumps({'valid': ok, 'reason_code': dbg.get('reason_code'), 'debug': dbg}, ensure_ascii=False))
    raise SystemExit(0 if ok else 2)


def cmd_verify_chain(args):
    secret = load_secret(args.secret)
    trusted = _load_trusted_kids(args.trusted_kids)
    ledger = Path(args.ledger)
    rows = []
    seen_ids = set(); seen_nonces = set(); seq_seen = set()
    for i, ln in enumerate(ledger.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            print(json.dumps({'valid': False, 'reason_code': 'INVALID_SCHEMA', 'fail_index': i, 'reason': 'invalid_json'})); raise SystemExit(2)
        rows.append(r)

    prev_hash = None
    expected_seq = None
    for i, r in enumerate(rows):
        ok, dbg = verify_receipt(r, secret, trusted_kids=trusted, max_clock_skew_sec=args.max_clock_skew_sec)
        if not ok:
            print(json.dumps({'valid': False, 'reason_code': dbg.get('reason_code', 'INVALID_SCHEMA'), 'fail_index': i, 'fail_seq': r.get('seq'), 'debug': dbg}, ensure_ascii=False)); raise SystemExit(2)

        rid = r.get('decision_id')
        nonce = r.get('nonce')
        if rid and rid in seen_ids:
            print(json.dumps({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'fail_seq': r.get('seq'), 'reason': 'duplicate_decision_id'})); raise SystemExit(2)
        if nonce and nonce in seen_nonces:
            print(json.dumps({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'fail_seq': r.get('seq'), 'reason': 'duplicate_nonce_replay'})); raise SystemExit(2)
        if rid: seen_ids.add(rid)
        if nonce: seen_nonces.add(nonce)

        # optional sequence validation
        seq = r.get('seq')
        if seq is not None:
            try:
                seq = int(seq)
            except Exception:
                print(json.dumps({'valid': False, 'reason_code': 'INVALID_SCHEMA', 'fail_index': i, 'reason': 'seq_not_int'})); raise SystemExit(2)
            if seq in seq_seen:
                print(json.dumps({'valid': False, 'reason_code': 'REPLAY', 'fail_index': i, 'fail_seq': seq, 'reason': 'duplicate_seq'})); raise SystemExit(2)
            seq_seen.add(seq)
            if expected_seq is None:
                expected_seq = seq
            elif seq != expected_seq + 1:
                print(json.dumps({'valid': False, 'reason_code': 'SEQ_GAP', 'fail_index': i, 'expected_seq': expected_seq + 1, 'got_seq': seq})); raise SystemExit(2)
            expected_seq = seq

        cur_prev = (r.get('hashes') or {}).get('prev_receipt_sha256')
        if i == 0:
            if cur_prev not in (None, '', 'null'):
                print(json.dumps({'valid': False, 'reason_code': 'CHAIN_PREV_HASH_MISMATCH', 'fail_index': i, 'reason': 'genesis_prev_hash_must_be_null'})); raise SystemExit(2)
        else:
            if cur_prev != prev_hash:
                print(json.dumps({'valid': False, 'reason_code': 'CHAIN_PREV_HASH_MISMATCH', 'fail_index': i, 'fail_seq': r.get('seq'), 'expected': prev_hash, 'got': cur_prev})); raise SystemExit(2)

        prev_hash = (r.get('hashes') or {}).get('receipt_sha256')

    print(json.dumps({'valid': True, 'reason_code': 'OK', 'checked': len(rows), 'last_hash': prev_hash}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(prog='receiptos')
    sp = ap.add_subparsers(dest='cmd', required=True)

    a = sp.add_parser('sign')
    a.add_argument('--input', required=True)
    a.add_argument('--output')
    a.add_argument('--kid', default='local-dev-key')
    a.add_argument('--secret', help='secret literal or path to file')
    a.add_argument('--ledger', default='receiptos_mvp/examples/decision_receipts.jsonl')
    a.add_argument('--chain', action='store_true')
    a.add_argument('--append', action='store_true')
    a.set_defaults(func=cmd_sign)

    b = sp.add_parser('verify')
    b.add_argument('--input', required=True)
    b.add_argument('--secret', help='secret literal or path to file')
    b.add_argument('--trusted-kids', help='comma list or json file with allowed key_ids')
    b.add_argument('--max-clock-skew-sec', type=int, help='optional absolute clock skew check')
    b.set_defaults(func=cmd_verify)

    c = sp.add_parser('verify-chain')
    c.add_argument('--ledger', required=True)
    c.add_argument('--secret', help='secret literal or path to file')
    c.add_argument('--trusted-kids', help='comma list or json file with allowed key_ids')
    c.add_argument('--max-clock-skew-sec', type=int, help='optional absolute clock skew check')
    c.set_defaults(func=cmd_verify_chain)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

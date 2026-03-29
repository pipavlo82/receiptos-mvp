from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from receiptos_mvp.src.receiptos import sign_receipt, verify_receipt

SECRET = 'demo-secret-change-me'


def _base_payload(seq: int | None = None):
    p = {
        'actor': {'agent': 'test-agent', 'policy': 'test-policy'},
        'inputs': {'context_hash': 'ctx', 'source_refs': ['test']},
        'tool_call': {'name': 'tool_x', 'input': {'a': 1}, 'output': {'b': 2}},
        'decision': {'action': 'go', 'confidence': 0.7},
        'evidence': [{'kind': 'rule', 'value': 'ok', 'weight': 0.5}],
        'nonce': f'nonce-{seq if seq is not None else "x"}'
    }
    if seq is not None:
        p['seq'] = seq
    return p


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')


def _run_verify_chain(ledger: Path):
    import subprocess
    p = subprocess.run([
        'python3', '-m', 'receiptos_mvp.src.cli', 'verify-chain',
        '--ledger', str(ledger)
    ], capture_output=True, text=True)
    out = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else '{}'
    try:
        j = json.loads(out)
    except Exception:
        j = {'valid': False, 'reason_code': 'INVALID_SCHEMA'}
    return p.returncode, j


def test_tamper_reason_code():
    r = sign_receipt(_base_payload(), SECRET)
    r['decision']['confidence'] = 0.1
    ok, dbg = verify_receipt(r, SECRET)
    assert ok is False
    assert dbg.get('reason_code') == 'TAMPER'


def test_bad_signature_reason_code():
    r = sign_receipt(_base_payload(), SECRET)
    r['signature']['sig_hex'] = '00' * 32
    ok, dbg = verify_receipt(r, SECRET)
    assert ok is False
    assert dbg.get('reason_code') == 'BAD_SIGNATURE'


def test_untrusted_signer_reason_code():
    r = sign_receipt(_base_payload(), SECRET, key_id='kid-A')
    ok, dbg = verify_receipt(r, SECRET, trusted_kids={'kid-B'})
    assert ok is False
    assert dbg.get('reason_code') == 'UNTRUSTED_SIGNER'


def test_clock_skew_reason_code():
    r = sign_receipt(_base_payload(), SECRET)
    r['ts_utc'] = '2000-01-01T00:00:00Z'
    # recompute signature for modified payload to isolate CLOCK_SKEW
    r = sign_receipt({k: v for k, v in r.items() if k not in {'hashes', 'signature'}}, SECRET, key_id='local-dev-key', prev_hash=None)
    ok, dbg = verify_receipt(r, SECRET, max_clock_skew_sec=10)
    assert ok is False
    assert dbg.get('reason_code') == 'CLOCK_SKEW'


def test_invalid_schema_reason_code():
    bad = {'actor': {'agent': 'x'}}
    ok, dbg = verify_receipt(bad, SECRET)
    assert ok is False
    assert dbg.get('reason_code') == 'INVALID_SCHEMA'


def test_chain_prev_hash_mismatch_reason_code():
    r1 = sign_receipt(_base_payload(seq=1), SECRET, prev_hash=None)
    r2 = sign_receipt(_base_payload(seq=2), SECRET, prev_hash='wrong-prev-hash')
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / 'l.jsonl'
        _write_jsonl(ledger, [r1, r2])
        rc, out = _run_verify_chain(ledger)
        assert rc != 0
        assert out.get('reason_code') == 'CHAIN_PREV_HASH_MISMATCH'
        assert out.get('fail_index') == 1


def test_seq_gap_reason_code():
    r1 = sign_receipt(_base_payload(seq=1), SECRET, prev_hash=None)
    r2 = sign_receipt(_base_payload(seq=3), SECRET, prev_hash=r1['hashes']['receipt_sha256'])
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / 'l.jsonl'
        _write_jsonl(ledger, [r1, r2])
        rc, out = _run_verify_chain(ledger)
        assert rc != 0
        assert out.get('reason_code') == 'SEQ_GAP'
        assert out.get('fail_index') == 1


def test_replay_reason_code():
    p = _base_payload(seq=1)
    p['decision_id'] = 'fixed-id'
    p['nonce'] = 'fixed-nonce'
    r1 = sign_receipt(p, SECRET, prev_hash=None)
    # duplicate id/nonce but valid link hash
    p2 = copy.deepcopy(p)
    p2['seq'] = 2
    r2 = sign_receipt(p2, SECRET, prev_hash=r1['hashes']['receipt_sha256'])
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / 'l.jsonl'
        _write_jsonl(ledger, [r1, r2])
        rc, out = _run_verify_chain(ledger)
        assert rc != 0
        assert out.get('reason_code') == 'REPLAY'
        assert out.get('fail_index') == 1

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path('/mnt/d/prop_bot')


def run(cmd: list[str]):
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_sign_verify_chain():
    ledger = ROOT / 'receiptos_mvp/examples/test_smoke_ledger.jsonl'
    if ledger.exists():
        ledger.unlink()

    rc, out, err = run([
        'python3', '-m', 'receiptos_mvp.src.cli', 'sign',
        '--input', 'receiptos_mvp/examples/sample_tool_payload.json',
        '--output', 'receiptos_mvp/examples/sample_receipt.json',
        '--chain', '--append',
        '--ledger', str(ledger),
    ])
    assert rc == 0, (out, err)

    rc, out, err = run([
        'python3', '-m', 'receiptos_mvp.src.cli', 'verify',
        '--input', 'receiptos_mvp/examples/sample_receipt.json',
    ])
    assert rc == 0, (out, err)

    rc, out, err = run([
        'python3', '-m', 'receiptos_mvp.src.cli', 'verify-chain',
        '--ledger', str(ledger),
    ])
    assert rc == 0, (out, err)


def test_codex_demo():
    rc, out, err = run(['python3', 'receiptos_mvp/examples/codex_agent_demo.py'])
    assert rc == 0, (out, err)
    assert 'original decision verified' in out
    assert 'tampered tool output detected' in out


def test_tamper_demo():
    rc, out, err = run(['python3', 'receiptos_mvp/examples/tamper_demo.py'])
    assert rc == 0, (out, err)
    assert '"ok_after": false' in out.lower()


def test_replay_demo():
    rc, out, err = run(['python3', 'receiptos_mvp/examples/replay_demo.py'])
    assert rc == 0, (out, err)
    assert 'replay-fixed-id' in out


def test_api_replay_demo():
    rc, out, err = run(['python3', 'receiptos_mvp/examples/api_replay_demo.py'])
    assert rc == 0, (out, err)
    assert 'first ingest accepted' in out
    assert 'rejected as replay' in out
    assert '"reason_code": "REPLAY"' in out


def test_demo_all():
    rc, out, err = run(['python3', 'receiptos_mvp/examples/demo_all.py'])
    assert rc == 0, (out, err)
    assert '[PASS] sign' in out
    assert '[PASS] verify' in out
    assert '[PASS] codex_demo' in out
    assert '[PASS] tamper_detection' in out
    assert '[PASS] replay_detection' in out
    assert '[PASS] verify_chain' in out

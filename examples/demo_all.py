#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path('/mnt/d/prop_bot')


def run(name: str, cmd: list[str]):
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    ok = p.returncode == 0
    print(f"\n=== {name} ===")
    if p.stdout.strip():
        print(p.stdout.strip())
    if not ok and p.stderr.strip():
        print(p.stderr.strip())
    return ok


def main():
    checks = []
    ledger = ROOT / 'receiptos_mvp/examples/demo_all_ledger.jsonl'
    if ledger.exists():
        ledger.unlink()

    checks.append(("sign", run("sign", [
        'python3', '-m', 'receiptos_mvp.src.cli', 'sign',
        '--input', 'receiptos_mvp/examples/sample_tool_payload.json',
        '--output', 'receiptos_mvp/examples/sample_receipt.json',
        '--chain', '--append',
        '--ledger', str(ledger)
    ])))

    checks.append(("verify", run("verify", [
        'python3', '-m', 'receiptos_mvp.src.cli', 'verify',
        '--input', 'receiptos_mvp/examples/sample_receipt.json'
    ])))

    checks.append(("codex_demo", run("codex_demo", [
        'python3', 'receiptos_mvp/examples/codex_agent_demo.py'
    ])))

    checks.append(("tamper_detection", run("tamper_detection", [
        'python3', 'receiptos_mvp/examples/tamper_demo.py'
    ])))

    checks.append(("replay_detection", run("replay_detection", [
        'python3', 'receiptos_mvp/examples/replay_demo.py'
    ])))

    checks.append(("verify_chain", run("verify_chain", [
        'python3', '-m', 'receiptos_mvp.src.cli', 'verify-chain',
        '--ledger', str(ledger)
    ])))

    print("\n=== SUMMARY ===")
    all_ok = True
    for name, ok in checks:
        print(f"[{ 'PASS' if ok else 'FAIL' }] {name}")
        all_ok = all_ok and ok

    if not all_ok:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from receiptos import sign_receipt

SECRET='demo-secret-change-me'
base={
    'actor': {'agent':'demo','policy':'p1'},
    'inputs': {'context_hash':'ctx2'},
    'decision': {'action':'approve','confidence':0.73},
    'evidence': [{'kind':'rule','value':'ok','weight':0.6}],
    'decision_id': 'replay-fixed-id',
    'nonce': 'replay-fixed-nonce'
}
r=sign_receipt(base, SECRET, key_id='demo-k1')
# replay == same receipt submitted twice
print(json.dumps({'first_submit': r, 'second_submit_same': r, 'expected':'second should be rejected by duplicate decision_id/nonce policy'}, ensure_ascii=False, indent=2))

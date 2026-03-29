#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from receiptos import sign_receipt, verify_receipt

SECRET='demo-secret-change-me'
base={
    'actor': {'agent':'demo','policy':'p1'},
    'inputs': {'context_hash':'ctx1'},
    'decision': {'action':'approve','confidence':0.81},
    'evidence': [{'kind':'rule','value':'ok','weight':0.7}],
    'nonce': 'nonce-tamper-1'
}

signed=sign_receipt(base, SECRET, key_id='demo-k1')
ok_before, _ = verify_receipt(signed, SECRET)

# tamper payload post-sign
signed['decision']['confidence']=0.11
ok_after, dbg_after = verify_receipt(signed, SECRET)
print(json.dumps({'ok_before':ok_before,'ok_after':ok_after,'after_debug':dbg_after}, ensure_ascii=False, indent=2))

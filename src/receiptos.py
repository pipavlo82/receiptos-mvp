from __future__ import annotations
import hashlib, hmac, json, secrets
from datetime import datetime, timezone
from pathlib import Path


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _canon(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign_receipt(receipt: dict, secret: str, key_id: str = 'local-dev-key', prev_hash: str | None = None) -> dict:
    base = dict(receipt)
    base.setdefault('receipt_version', 'v1')
    base.setdefault('decision_id', secrets.token_hex(8))
    base.setdefault('ts_utc', now_utc_iso())

    unsigned = {k: v for k, v in base.items() if k not in {'hashes', 'signature'}}
    decision_sha = sha256_hex(_canon(unsigned))

    preimage = f"{decision_sha}|{prev_hash or ''}".encode('utf-8')
    receipt_sha = sha256_hex(preimage)
    sig_hex = hmac.new(secret.encode('utf-8'), preimage, hashlib.sha256).hexdigest()

    out = dict(unsigned)
    out['hashes'] = {
        'decision_sha256': decision_sha,
        'receipt_sha256': receipt_sha,
        'prev_receipt_sha256': prev_hash,
    }
    out['signature'] = {
        'alg': 'HMAC-SHA256',
        'key_id': key_id,
        'sig_hex': sig_hex,
    }
    return out


def _parse_dt(ts: str | None):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except Exception:
        return None


def _schema_like_check(r: dict) -> tuple[bool, str]:
    required = ['receipt_version', 'decision_id', 'ts_utc', 'actor', 'inputs', 'decision', 'evidence', 'hashes', 'signature']
    for k in required:
        if k not in r:
            return False, f'missing:{k}'
    if not isinstance(r.get('actor'), dict) or not isinstance(r.get('decision'), dict):
        return False, 'bad_types'
    if 'action' not in r['decision'] or 'confidence' not in r['decision']:
        return False, 'missing:decision.action_or_confidence'
    # tool_call is optional (backward compatible), but if present must include name/input/output
    tc = r.get('tool_call')
    if tc is not None:
        if not isinstance(tc, dict):
            return False, 'bad_types:tool_call'
        for k in ['name', 'input', 'output']:
            if k not in tc:
                return False, f'missing:tool_call.{k}'
    return True, 'ok'


def verify_receipt(
    receipt: dict,
    secret: str,
    trusted_kids: set[str] | None = None,
    max_clock_skew_sec: int | None = None,
) -> tuple[bool, dict]:
    r = dict(receipt)

    ok_schema, schema_note = _schema_like_check(r)
    if not ok_schema:
        return False, {
            'reason_code': 'INVALID_SCHEMA',
            'reason_detail': schema_note,
        }

    hashes = r.get('hashes', {})
    sig = (r.get('signature') or {}).get('sig_hex', '')
    prev_hash = hashes.get('prev_receipt_sha256')
    key_id = (r.get('signature') or {}).get('key_id')

    if trusted_kids is not None and key_id not in trusted_kids:
        return False, {
            'reason_code': 'UNTRUSTED_SIGNER',
            'reason_detail': f'key_id={key_id}',
        }

    if max_clock_skew_sec is not None:
        dt = _parse_dt(r.get('ts_utc'))
        if dt is None:
            return False, {'reason_code': 'INVALID_SCHEMA', 'reason_detail': 'bad ts_utc'}
        skew = abs((datetime.now(timezone.utc) - dt).total_seconds())
        if skew > max_clock_skew_sec:
            return False, {
                'reason_code': 'CLOCK_SKEW',
                'reason_detail': f'skew_sec={int(skew)} > {max_clock_skew_sec}',
            }

    unsigned = {k: v for k, v in r.items() if k not in {'hashes', 'signature'}}
    decision_sha = sha256_hex(_canon(unsigned))
    preimage = f"{decision_sha}|{prev_hash or ''}".encode('utf-8')
    receipt_sha = sha256_hex(preimage)
    expected_sig = hmac.new(secret.encode('utf-8'), preimage, hashlib.sha256).hexdigest()

    decision_sha_match = decision_sha == hashes.get('decision_sha256')
    receipt_sha_match = receipt_sha == hashes.get('receipt_sha256')
    signature_match = hmac.compare_digest(sig, expected_sig)

    if not decision_sha_match or not receipt_sha_match:
        return False, {
            'reason_code': 'TAMPER',
            'decision_sha_match': decision_sha_match,
            'receipt_sha_match': receipt_sha_match,
            'signature_match': signature_match,
            'computed_decision_sha256': decision_sha,
            'computed_receipt_sha256': receipt_sha,
        }
    if not signature_match:
        return False, {
            'reason_code': 'BAD_SIGNATURE',
            'decision_sha_match': decision_sha_match,
            'receipt_sha_match': receipt_sha_match,
            'signature_match': signature_match,
            'computed_decision_sha256': decision_sha,
            'computed_receipt_sha256': receipt_sha,
        }

    return True, {
        'reason_code': 'OK',
        'decision_sha_match': True,
        'receipt_sha_match': True,
        'signature_match': True,
        'computed_decision_sha256': decision_sha,
        'computed_receipt_sha256': receipt_sha,
    }


def append_jsonl(fp: Path, obj: dict):
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')

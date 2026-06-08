import pickle
from pathlib import Path
import time


_BASE = Path(__file__).resolve().parent
CACHE_DIR = _BASE / '.cache'


def _key_to_path(key: str) -> Path:
    safe = "".join([c if c.isalnum() or c in ('-', '_') else '_' for c in key])
    return CACHE_DIR / f"{safe}.pkl"


def set_cache(key: str, obj, ttl_seconds: int = 3600):
    CACHE_DIR.mkdir(exist_ok=True)
    p = _key_to_path(key)
    payload = {'ts': int(time.time()), 'ttl': int(ttl_seconds), 'obj': obj}
    with p.open('wb') as f:
        pickle.dump(payload, f)


def get_cache(key: str, ttl_seconds: int = None):
    CACHE_DIR.mkdir(exist_ok=True)
    p = _key_to_path(key)
    if not p.exists():
        return None
    try:
        with p.open('rb') as f:
            payload = pickle.load(f)
        ts = payload.get('ts', 0)
        ttl = payload.get('ttl', 0)
        if ttl_seconds is None:
            ttl_check = ttl
        else:
            ttl_check = int(ttl_seconds)
        if ttl_check <= 0:
            return payload.get('obj')
        if int(time.time()) - ts <= ttl_check:
            return payload.get('obj')
        return None
    except Exception:
        return None

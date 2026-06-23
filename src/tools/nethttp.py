"""Shared HTTP helper: requests.get with retry/backoff on transient failures.

Flaky externals (crt.sh timeouts, rdap.org read-timeouts, HackerTarget 429s, generic
5xx) were killing pivots on the first failure. http_get retries transient errors with
linear backoff so a single blip doesn't lose a finding.
"""
import time

import requests

# Transient HTTP statuses worth a retry (rate-limit + server-side).
TRANSIENT_STATUS = {429, 500, 502, 503, 504}


def http_get(url, *, timeout=20, retries=2, backoff=1.5, **kwargs):
    """GET with retry/backoff. Retries on Timeout/ConnectionError and TRANSIENT_STATUS.
    Returns the final Response (even if it's still an error status); raises only if every
    attempt raised a connection-level exception."""
    last_exc = None
    resp = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        if resp.status_code in TRANSIENT_STATUS and attempt < retries:
            time.sleep(backoff * (attempt + 1))
            continue
        return resp
    if resp is not None:
        return resp
    raise last_exc  # pragma: no cover

#!/usr/bin/env python3
"""CLI adapter that POSTs one normalized case to /invoke."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    case = json.load(sys.stdin)
    base_url = os.environ.get("AGENT_ASSURANCE_HTTP_URL", "http://127.0.0.1:8088")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/invoke",
        data=json.dumps(case).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

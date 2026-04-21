"""Unified notification helper for Miracle Coins backend.

Usage:
    from app.notifications import notify
    notify("**Something happened!**\\nDetails here")
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

if load_dotenv:
    # Ensure notifications can read webhook config even when called outside main.py.
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def notify(content: str) -> None:
    """Send a message to the configured Discord webhook. Never raises."""
    import sys
    url = (
        os.getenv('DISCORD_WEBHOOK_URL', '').strip()
        or os.getenv('DISCORD_WEBHOOK', '').strip()
        or os.getenv('ORDER_DISCORD_WEBHOOK_URL', '').strip()
    )
    if not url:
        print('[notifications] DISCORD_WEBHOOK_URL not set — skipping notify', file=sys.stderr)
        return
    try:
        # Discord content limit is 2000; leave headroom for formatting.
        safe_content = (content or '').strip()
        if len(safe_content) > 1900:
            safe_content = safe_content[:1890] + '...'
        body = json.dumps({'content': safe_content}).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={
                'Content-Type': 'application/json',
                # Discord/Cloudflare may block default Python urllib signature (403 code 1010).
                'User-Agent': 'MiracleCoinsBot/1.0 (+https://miracle-coins.com)',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f'[notifications] Discord webhook sent, status={resp.status}', file=sys.stderr)
    except Exception as exc:
        print(f'[notifications] Discord webhook FAILED: {exc}', file=sys.stderr)

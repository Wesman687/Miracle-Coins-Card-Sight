"""Unified notification helper for Miracle Coins backend.

Usage:
    from app.notifications import notify
    notify("**Something happened!**\\nDetails here")
"""
from __future__ import annotations

import json
import os
import urllib.request


def notify(content: str) -> None:
    """Send a message to the configured Discord webhook. Never raises."""
    import sys
    url = os.getenv('DISCORD_WEBHOOK_URL', '')
    if not url:
        print('[notifications] DISCORD_WEBHOOK_URL not set — skipping notify', file=sys.stderr)
        return
    try:
        body = json.dumps({'content': content}).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f'[notifications] Discord webhook sent, status={resp.status}', file=sys.stderr)
    except Exception as exc:
        print(f'[notifications] Discord webhook FAILED: {exc}', file=sys.stderr)

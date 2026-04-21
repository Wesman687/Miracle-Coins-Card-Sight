"""
sync_uploads.py — push all local uploads/ files to the production server.

Default (recommended): PUT preserves filenames (matches DB URLs). Requires the
sync-upload route on the server.

    python sync_uploads.py

If production does not have that route yet, use legacy mode (POST upload-image
assigns new random filenames). Pair with --update-db so coin_images URLs match.

    python sync_uploads.py --legacy --update-db

Requires MANAGE_TOKEN in .env. Optional: SYNC_API_BASE, DATABASE_URL (for --update-db).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv(
    "SYNC_API_BASE",
    "https://server.stream-lineai.com/miracle-coins/api/v1",
).rstrip("/")
MANAGE_TOKEN = os.getenv("MANAGE_TOKEN", "manage-token")
UPLOADS_DIR = Path(__file__).parent / "uploads"

HEADERS = {"Authorization": f"Bearer {MANAGE_TOKEN}"}

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _mime(path: Path) -> str:
    if path.suffix.lower() in (".jpg", ".jpeg"):
        return "image/jpeg"
    return f"image/{path.suffix.lower().lstrip('.')}"


def _update_coin_image_url(conn, basename: str, new_url: str) -> int:
    import psycopg2.extensions

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE coin_images
            SET url = %s
            WHERE split_part(rtrim(url, '/'), '/', -1) = %s
            """,
            (new_url, basename),
        )
        return cur.rowcount


def main() -> int:
    p = argparse.ArgumentParser(description="Sync local backend/uploads to production.")
    p.add_argument(
        "--legacy",
        action="store_true",
        help="Use POST /storefront/upload-image (new random filenames). Use --update-db to fix DB.",
    )
    p.add_argument(
        "--update-db",
        action="store_true",
        help="After each legacy upload, set coin_images.url to the new URL (needs DATABASE_URL).",
    )
    args = p.parse_args()

    if args.update_db and not args.legacy:
        print("Error: --update-db only applies with --legacy.", file=sys.stderr)
        return 2

    files = sorted(
        f
        for f in UPLOADS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    )

    if not files:
        print("No image files found in uploads/")
        return 0

    try:
        health = requests.get(f"{SERVER}/health", timeout=10)
        print(f"API health: {health.status_code}  ({SERVER}/health)\n")
    except Exception as exc:
        print(f"Warning: could not reach {SERVER}/health: {exc}\n")

    conn = None
    if args.update_db:
        db_url = os.getenv("DATABASE_URL", "").strip()
        if not db_url:
            print("Error: DATABASE_URL must be set for --update-db.", file=sys.stderr)
            return 2
        import psycopg2

        conn = psycopg2.connect(db_url)
        conn.autocommit = False

    print(f"Mode: {'legacy POST upload-image' if args.legacy else 'PUT sync-upload (preserve names)'}\n")
    print(f"Found {len(files)} local image(s) to sync...\n")

    ok = skipped = failed = db_updated = 0

    for path in files:
        mime = _mime(path)
        try:
            with open(path, "rb") as fp:
                if args.legacy:
                    resp = requests.post(
                        f"{SERVER}/storefront/upload-image",
                        headers=HEADERS,
                        files={"file": (path.name, fp, mime)},
                        timeout=120,
                    )
                else:
                    resp = requests.put(
                        f"{SERVER}/storefront/admin/sync-upload/{path.name}",
                        headers=HEADERS,
                        files={"file": (path.name, fp, mime)},
                        timeout=120,
                    )

            if resp.status_code == 200:
                data = resp.json() if resp.content else {}
                if not args.legacy and data.get("status") == "exists":
                    print(f"  SKIP  {path.name} (already on server)")
                    skipped += 1
                    continue
                if args.legacy:
                    new_url = (data or {}).get("url")
                    print(f"  UP    {path.name}  ->  {new_url or '(no url in response)'}")
                    ok += 1
                    if args.update_db and conn and new_url:
                        n = _update_coin_image_url(conn, path.name, new_url)
                        conn.commit()
                        db_updated += n
                        if n == 0:
                            print(f"       (no coin_images row matched basename {path.name})")
                else:
                    print(f"  UP    {path.name}")
                    ok += 1
            else:
                snippet = (resp.text or "")[:200].replace("\n", " ")
                print(f"  FAIL  {path.name}  ->  {resp.status_code}: {snippet}")
                failed += 1
        except Exception as exc:
            if conn:
                conn.rollback()
            print(f"  ERR   {path.name}  ->  {exc}")
            failed += 1

    if conn:
        conn.close()

    print(f"\nDone. Uploaded: {ok}  Skipped: {skipped}  Failed: {failed}")
    if args.update_db:
        print(f"DB rows updated (coin_images): {db_updated}")

    if failed and ok == 0 and skipped == 0 and not args.legacy:
        print(
            "\nHint: If status was 404 for every file, production may not have the sync-upload route yet. "
            "Either deploy the latest backend and re-run, or run:  python sync_uploads.py --legacy --update-db"
        )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

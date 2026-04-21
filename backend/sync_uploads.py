"""
sync_uploads.py — push all local uploads/ files to the production server.

Run once from the backend directory:
    python sync_uploads.py

Files that already exist on the server are skipped.
"""
import os
import sys
from pathlib import Path
import requests

SERVER = "https://server.stream-lineai.com/miracle-coins/api/v1"
MANAGE_TOKEN = os.getenv("MANAGE_TOKEN", "manage-token")
UPLOADS_DIR = Path(__file__).parent / "uploads"

HEADERS = {"Authorization": f"Bearer {MANAGE_TOKEN}"}

image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

files = [f for f in UPLOADS_DIR.iterdir() if f.is_file() and f.suffix.lower() in image_exts]

if not files:
    print("No image files found in uploads/")
    sys.exit(0)

print(f"Found {len(files)} local image(s) to sync...\n")

ok = skipped = failed = 0

for f in sorted(files):
    mime = "image/jpeg" if f.suffix.lower() in ('.jpg', '.jpeg') else f"image/{f.suffix.lstrip('.')}"
    try:
        with open(f, "rb") as fp:
            resp = requests.put(
                f"{SERVER}/storefront/admin/sync-upload/{f.name}",
                headers=HEADERS,
                files={"file": (f.name, fp, mime)},
                timeout=30,
            )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "exists":
                print(f"  SKIP  {f.name} (already on server)")
                skipped += 1
            else:
                print(f"  UP    {f.name}")
                ok += 1
        else:
            print(f"  FAIL  {f.name}  →  {resp.status_code}: {resp.text[:120]}")
            failed += 1
    except Exception as exc:
        print(f"  ERR   {f.name}  →  {exc}")
        failed += 1

print(f"\nDone. Uploaded: {ok}  Skipped: {skipped}  Failed: {failed}")

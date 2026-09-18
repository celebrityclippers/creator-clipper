"""
pipeline.py
============
Entry point for the edit stage of the clip pipeline.

Usage:
    python pipeline.py "https://youtube.com/watch?v=SOURCE_ID" "Your hook text"

This script does NOT decide what content to source — you pass in a
specific URL each run, and you're responsible for having the right
to use it. It does NOT publish anything either; it stops at
review_queue/ with a manifest.json for you (or approve_and_publish.py)
to look at before anything goes live.
"""

import sys
from smart_editor import run_smart_edit


def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <source_url> [hook_text]")
        sys.exit(1)

    source_url = sys.argv[1]
    hook_text = sys.argv[2] if len(sys.argv) > 2 else "Wait for it..."

    print(f"[*] Running smart edit on: {source_url}")
    results = run_smart_edit(
        source_url_or_path=source_url,
        hook_text=hook_text,
        review_dir="review_queue",
        is_url=True,
    )

    print(f"\n[+] Done. {len(results)} clip(s) staged in review_queue/.")
    print("[+] Next step: python approve_and_publish.py")


if __name__ == "__main__":
    main()

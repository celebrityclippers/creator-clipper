"""
approve_and_publish.py
========================
Reads review_queue/manifest.json, shows you each staged clip, and
only uploads the ones you explicitly approve. This is the one place
in the whole pipeline that's allowed to call YouTubePublisher.

Usage:
    python approve_and_publish.py
"""

import json
import os
from youtube_publisher import YouTubePublisher

REVIEW_DIR = "review_queue"
MANIFEST_PATH = os.path.join(REVIEW_DIR, "manifest.json")


def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"[!] No manifest found at {MANIFEST_PATH}. Run pipeline.py first.")
        return

    with open(MANIFEST_PATH) as f:
        clips = json.load(f)

    if not clips:
        print("[!] No clips in manifest.")
        return

    publisher = None  # lazily created only once you approve something

    for clip in clips:
        print("\n" + "=" * 50)
        print(f"Clip #{clip['index']}  (highlight score: {clip['highlight_score']:.1f})")
        print(f"  Time range: {clip['start']:.1f}s - {clip['end']:.1f}s")
        print(f"  Widescreen: {clip['widescreen_path']}")
        print(f"  Vertical:   {clip['vertical_path']}")
        print(f"  Transcript preview: {clip['transcript_preview'][:200]}")

        choice = input(
            "\nApprove this clip? [w=widescreen only / v=vertical only / "
            "b=both / n=skip]: "
        ).strip().lower()

        if choice not in ("w", "v", "b"):
            print("[-] Skipped.")
            continue

        title = input("Title for this upload: ").strip()
        description = input("Description: ").strip()
        tags_raw = input("Tags (comma-separated, optional): ").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] or None

        privacy = input(
            "Privacy status [private/unlisted/public] (default private): "
        ).strip().lower() or "private"

        if publisher is None:
            publisher = YouTubePublisher()

        if choice in ("w", "b"):
            publisher.upload_video(
                file_path=clip["widescreen_path"],
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy,
            )
        if choice in ("v", "b"):
            publisher.upload_video(
                file_path=clip["vertical_path"],
                title=f"{title} #shorts",
                description=description,
                tags=tags,
                privacy_status=privacy,
            )

    print("\n[+] Review pass complete.")


if __name__ == "__main__":
    main()

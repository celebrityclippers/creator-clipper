"""
publish_clip.py
=================
Non-interactive publisher for a single, already-reviewed clip file.
Meant for the CI "publish" workflow, where you as a human have
already downloaded and watched the clip from the stage_clips artifact
and are now deliberately telling it to go live.

Usage:
    python publish_clip.py <file_path> <title> <description> <privacy> <confirm>

The final argument must be exactly the string CONFIRM or the script
refuses to upload anything. This exists so a workflow can't be
triggered accidentally or by a stray automation with no one actually
having reviewed the file first.
"""

import sys
from youtube_publisher import YouTubePublisher


def main():
    if len(sys.argv) != 6:
        print(
            "Usage: python publish_clip.py <file_path> <title> <description> "
            "<privacy: private|unlisted|public> <confirm: CONFIRM>"
        )
        sys.exit(1)

    file_path, title, description, privacy, confirm = sys.argv[1:6]

    if confirm != "CONFIRM":
        print("[!] Refusing to publish: confirmation string did not match 'CONFIRM'.")
        print("[!] This is a safety gate — pass CONFIRM only after you've watched the clip.")
        sys.exit(1)

    if privacy not in ("private", "unlisted", "public"):
        print("[!] privacy must be one of: private, unlisted, public")
        sys.exit(1)

    publisher = YouTubePublisher()
    publisher.upload_video(
        file_path=file_path,
        title=title,
        description=description,
        privacy_status=privacy,
    )


if __name__ == "__main__":
    main()

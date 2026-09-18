"""
youtube_publisher.py
=====================
Handles authenticated uploads to YouTube via the Data API v3.
Only publishes what you explicitly tell it to — this module never
decides on its own what gets uploaded.
"""

import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class YouTubePublisher:
    def __init__(self, token_path="token.json"):
        if not os.path.exists(token_path):
            raise FileNotFoundError(
                f"Missing crucial token file: {token_path}. Run get_token.py first."
            )

        self.credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(
            token_path,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
            ],
        )
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def upload_video(
        self,
        file_path,
        title,
        description,
        tags=None,
        privacy_status="private",
        category_id="22",
    ):
        """
        Uploads a video. Defaults to privacyStatus='private' on purpose —
        change to 'public' explicitly once you've confirmed the upload
        looks right, so a bug can't accidentally make something world-visible.
        """
        if not os.path.exists(file_path):
            print(f"[!] Target file not found: {file_path}")
            return None

        print(f"[*] Initiating YouTube upload for: {file_path}")

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            file_path, mimetype="video/mp4", chunksize=1024 * 1024, resumable=True
        )

        request = self.youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[*] Uploading progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"[++] Success! Watch at: https://youtube.com/watch?v={video_id}")
        return video_id


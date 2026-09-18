import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubePublisher:
    def __init__(self, token_path="token.json"):
        if not os.path.exists(token_path):
            raise FileNotFoundError(f"Missing crucial token file: {token_path}")
            
        # Load the authentication token generated from Termux
        self.credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(token_path)
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def upload_video(self, file_path, title, description, tags=None, is_short=False):
        """Uploads video files to YouTube using a structured chunked protocol."""
        if not os.path.exists(file_path):
            print(f"[!] Target file not found: {file_path}")
            return None

        print(f"[*] Initiating YouTube upload for: {file_path}")
        
        body = {
            "snippet": {
                "title": title[:100],  # YouTube Max Title limit rule restriction
                "description": description,
                "tags": tags or ["clipper", "automation", "viral"],
                "categoryId": "22"  # People & Blogs category code
            },
            "status": {
                "privacyStatus": "public",  # Set to 'public' for automated distribution
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            file_path, 
            mimetype="video/mp4", 
            chunksize=1024*1024, 
            resumable=True
        )
        
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[*] Uploading progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        print(f"[++] Success! Video uploaded successfully. Watch at: https://youtu.be{video_id}")
        return video_id


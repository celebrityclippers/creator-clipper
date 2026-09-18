import os
import glob
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- SMART IMPORT GUARD FOR PLAYWRIGHT ---
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ModuleNotFoundError:
    PLAYWRIGHT_AVAILABLE = False
# -----------------------------------------

class SocialPublisher:
    def __init__(self, credentials_path="client_secrets.json"):
        self.credentials_path = credentials_path
        # CORRECT FIXED SCOPE: Explicitly using the full www subdomain URL
        self.yt_scopes = ["https://googleapis.com"]

    def upload_to_youtube(self, video_path, title, description):
        """
        Authenticates and uploads a short video directly to YouTube Shorts.
        Uses a local redirect loop to fetch tokens safely inside Termux.
        """
        print("📺 Authenticating with YouTube Data API...")
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.yt_scopes)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 YouTube session expired. Refreshing authorization token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print("❌ Error: 'client_secrets.json' not found! Make sure it's placed in this folder.")
                    return
                
                print("🔑 Generating modern Google OAuth server link...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.yt_scopes)
                
                # --- FIXED METHOD STRATEGY: MATCHES GOOGLE'S EXACT ARGUMENT LAYOUT ---
                # This drops keyword parameter layout errors and forces a pristine connection link.
                creds = flow.run_local_server(
                    host='localhost',
                    port=8080,
                    open_browser=False
                )
                
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["shorts", "mrbeast", "ishowspeed", "comparison", "viral"],
                "categoryId": "24" 
            },
            "status": {
                "privacyStatus": "public",  
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        print(f"📤 Uploading file target {video_path} to YouTube Shorts pipeline...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"📊 YouTube Progress Status: {int(status.progress() * 100)}%")
        print(f"✅ Live on YouTube! Video Resource ID: {response['id']}")

    def upload_to_meta_via_session(self, platform, video_path):
        if not PLAYWRIGHT_AVAILABLE:
            print(f"⚠️ Playwright is not installed locally. Skipping {platform.upper()} browser automation.")
            return

        print(f"🌐 Running Playwright Session Automation for {platform.upper()}...")
        if not os.path.exists("playwright-session.json"):
            print("❌ Meta tracking layer missing! 'playwright-session.json' not found. Skipping.")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="playwright-session.json")
            page = context.new_page()
            page.goto("https://instagram.com" if platform.lower() == "instagram" else "https://facebook.com")
            browser.close()

if __name__ == "__main__":
    publisher = SocialPublisher()
    
    # FORCING OAUTH LOGIN: Passing a placeholder so it executes without checking output folders
    print("🚀 Forcing local YouTube authentication setup loop...")
    publisher.upload_to_youtube(
        video_path="dummy_file.mp4", 
        title="Test Title", 
        description="Test Description"
    )



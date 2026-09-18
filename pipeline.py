import os
import random
import subprocess
from yt_dlp import YoutubeDL
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. YOUTUBE API PUBLISHER ENGINE
# ==========================================
class YouTubePublisher:
    def __init__(self, token_path="token.json"):
        if not os.path.exists(token_path):
            raise FileNotFoundError(f"Missing crucial token file: {token_path}")
            
        # Load the authentication token securely decoded by GitHub Secrets
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
        print(f"[++] Success! Video uploaded successfully. Watch at: https://youtu.{video_id}")
        return video_id


# ==========================================
# 2. DYNAMIC SCOUTING & MEDIA PROCESSING PIPELINE
# ==========================================
class AutopilotClipperPipeline:
    def __init__(self, download_dir="downloads", output_dir="output"):
        self.download_dir = download_dir
        self.output_dir = output_dir
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    def discover_viral_target(self):
        """Autopilot Scouting Engine: Dynamically queries top global streaming hubs to select viral source nodes."""
        print("[*] Autopilot Sourcing Phase: Scanning global trending hubs...")
        
        # Extended high-engagement focus feeds pool
        scouting_pools = [
            "https://youtube.com", # YouTube Gaming Trends
            "https://youtube.com",                              # High-engagement gaming hub
            "https://youtube.com",             # High-engagement clip hub
            "https://youtube.com",              # Viral internet clips
            "https://youtube.com",                   # Twitch commentary highlights
            "https://youtube.com",                      # Tech & PC gaming trends
            "https://youtube.com",                   # Streamer specific clips
            "https://youtube.com"                            # High viral reach content creator
        ]
        
        selected_feed = random.choice(scouting_pools)
        print(f"[*] Scouting targeted platform target: {selected_feed}")
        
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'playlistend': 5, # Scrape the top 5 newest/hottest clips to choose from
            'quiet': True
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(selected_feed, download=False)
                if 'entries' in info and info['entries']:
                    valid_videos = [e for e in info['entries'] if e.get('url')]
                    chosen = random.choice(valid_videos)
                    
                    video_url = chosen['url']
                    if not video_url.startswith('http'):
                        video_url = f"https://youtube.com{video_url}"
                        
                    video_title = chosen.get('title', 'Viral Clip Highlight')
                    print(f"[++] Autopilot discovered active media node target: {video_url} - {video_title}")
                    return video_url, video_title
        except Exception as e:
            print(f"[!] Scouting failure on dynamic pool endpoint: {e}")
            
        # Hard fallback anchor URL to prevent workflow crashing if scraping gets rate-limited
        return "https://youtube.comdQw4w9WgXcQ", "Trending Global Clip Setup"

    def download_viral_segment(self, url):
        """Slices out a high-intensity mid-video chunk using precise server-side seek flags."""
        output_raw = os.path.join(self.download_dir, "raw_segment.mp4")
        print(f"[*] Extracting video block from stream timeline...")
        
        start_time = "00:02:00"  # Skips intro frames directly to catch core content
        duration = 45            # Captures a perfect clip runtime block

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': output_raw,
            'external_downloader': 'ffmpeg',
            'external_downloader_args': {
                'ffmpeg_args': ['-ss', start_time, '-t', str(duration)]
            },
            'quiet': True,
            'noplaylist': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_raw

    def process_media_formats(self, input_path):
        """Transforms the source segment into a 16:9 widescreen format and a 9:16 vertical grid short."""
        widescreen_path = os.path.join(self.output_dir, "widescreen_16_9.mp4")
        short_path = os.path.join(self.output_dir, "vertical_9_16.mp4")
        
        print("[*] Processing Output Phase 1: Rendering native widescreen clip...")
        subprocess.run(['ffmpeg', '-y', '-i', input_path, '-c', 'copy', widescreen_path], check=True)

        print("[*] Processing Output Phase 2: Center-cropping focal metrics for 9:16 Short...")
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-vf', 'crop=ih*(9/16):ih,scale=1080:1920',
            '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', short_path
        ], check=True)

        return widescreen_path, short_path

    def run_autopilot(self):
        """Orchestrates the entire hands-off execution pipeline loop."""
        # 1. Discover target video
        video_url, title = self.discover_viral_target()
        
        # 2. Slice required timeline chunk
        raw_clip = self.download_viral_segment(video_url)
        
        # 3. Process into dual layouts (16:9 and 9:16)
        widescreen, vertical_short = self.process_media_formats(raw_clip)
        
        # 4. Initialize publisher using local token.json file structure
        publisher = YouTubePublisher()
        clean_title = title.replace('"', '').replace("'", "")
        
        print("[*] Dispatching widescreen video to channel pipeline...")
        publisher.upload_video(
            file_path=widescreen,
            title=f"{clean_title} (Trending Moments)",
            description=f"Automated viral trending highlights compile. Sourced dynamically from: {video_url}",
            tags=["trending", "viral", "autopilot", "gaming"]
        )
        
        print("[*] Dispatching vertical short video to shorts loop...")
        publisher.upload_video(
            file_path=vertical_short,
            title=f"{clean_title} #shorts #viral",
            description="Dynamic vertical frame crop loop engineered by Celebrity-Clipper bot architectures.",
            tags=["shorts", "viral", "trending", "clips"],
            is_short=True
        )


if __name__ == "__main__":
    pipeline = AutopilotClipperPipeline()
    try:
        pipeline.run_autopilot()
    except Exception as e:
        print(f"[!] Autopilot structural system crash: {e}")

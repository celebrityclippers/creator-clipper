import os
import json
import random
import yt_dlp

class MultiFormatClipper:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        self.output_dir = "./assets"
        self.raw_dir = os.path.join(self.output_dir, "raw")
        
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "output"), exist_ok=True)

    def discover_and_download(self, search_query, filename_tag):
        print(f"🔍 Autonomously scanning web for: '{search_query}'...")
        outtmpl = os.path.join(self.raw_dir, f"{filename_tag}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'outtmpl': outtmpl,
            'default_search': f'ytsearch1:{search_query}',
            'download_ranges': lambda info, ctx: [{'start_time': 45, 'end_time': 60}],
            'force_keyframes_at_cuts': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([f"ytsearch1:{search_query}"])
                print(f"💾 Asset saved: {outtmpl}")
                return True
            except Exception as e:
                print(f"❌ Web scanner failed: {e}")
                return False

    def execute_pipeline(self):
        mode = random.choice(["individual", "comparison"])
        print(f"🎲 Pipeline Mode Triggered: [{mode.upper()}]")
        
        if mode == "individual":
            creator = random.choice(self.config["search_targets"])
            topic = random.choice(self.config["individual_topics"])
            search_query = f"{creator} {topic}"
            filename_tag = f"INDIVIDUAL_{creator.upper()}_{topic.replace(' ', '_')}"
            
            self.discover_and_download(search_query, filename_tag)
                
        else:
            comp_metric = random.choice(self.config["comparison_topics"])
            topic_name = comp_metric["topic"]
            keywords = comp_metric["keywords"]
            creator1, creator2 = self.config["search_targets"][0], self.config["search_targets"][1]
            
            print(f"📊 Starting Battle Metric: {topic_name}")
            
            tag1 = f"COMPARE_{creator1.upper()}_{keywords.split()[0]}"
            tag2 = f"COMPARE_{creator2.upper()}_{keywords.split()[0]}"
            
            self.discover_and_download(f"{creator1} {keywords}", tag1)
            self.discover_and_download(f"{creator2} {keywords}", tag2)

if __name__ == "__main__":
    clipper = MultiFormatClipper()
    clipper.execute_pipeline()

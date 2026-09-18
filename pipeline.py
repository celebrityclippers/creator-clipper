
"""
smart_editor.py
================
Transformative video editor for a clip pipeline.

Pipeline: source video -> highlight detection -> auto-transcribe ->
burned-in captions -> hook text overlay -> vertical + widescreen renders.

IMPORTANT — sourcing responsibility:
This module does NOT auto-scout or auto-select whose content to pull.
You must supply a source URL/file yourself, and you are responsible for
making sure you have the right to use it (your own recordings, licensed
clips, Creative Commons content, or explicit permission from the
creator). Editing a video does not, by itself, make it legal to use —
it just makes it transformative rather than a straight repost.

Requires:
    pip install yt-dlp faster-whisper numpy
    ffmpeg + ffprobe available on PATH
"""

import os
import json
import subprocess
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ==========================================
# 1. DOWNLOAD (explicit URL only — no auto-scouting)
# ==========================================

def download_source(url: str, download_dir: str = "downloads") -> str:
    """Downloads a full source video from an explicit URL you provide."""
    from yt_dlp import YoutubeDL

    os.makedirs(download_dir, exist_ok=True)
    out_path = os.path.join(download_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "outtmpl": out_path,
        "quiet": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# ==========================================
# 2. HIGHLIGHT DETECTION (audio-energy based)
# ==========================================

@dataclass
class Highlight:
    start: float
    end: float
    score: float


def _get_audio_levels(input_path: str, window_sec: float = 1.0) -> List[float]:
    """Uses ffmpeg's astats filter to get per-window RMS loudness."""
    cmd = [
        "ffmpeg", "-i", input_path,
        "-af", f"astats=metadata=1:reset={window_sec}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    levels = []
    for line in result.stderr.splitlines():
        if "RMS_level" in line and "Overall" not in line:
            try:
                val = float(line.split("=")[-1].strip())
                levels.append(val)
            except ValueError:
                continue
    return levels


def detect_highlights(
    input_path: str,
    clip_length: float = 25.0,
    top_n: int = 3,
    window_sec: float = 1.0,
) -> List[Highlight]:
    """
    Scores each window of the video by audio energy (loud reactions,
    hype, yelling tend to spike RMS loudness) and returns the top_n
    non-overlapping windows expanded to clip_length seconds each.
    """
    levels = _get_audio_levels(input_path, window_sec)
    if not levels:
        # Fallback: no usable audio stats, just take the start
        return [Highlight(0.0, clip_length, 0.0)]

    levels = np.array(levels)
    # RMS_level from astats is negative dB; louder = closer to 0
    scores = levels  # higher (less negative) = louder = more "hype"

    duration = len(levels) * window_sec
    half = clip_length / 2

    candidates = []
    for i, score in enumerate(scores):
        center = i * window_sec
        start = max(0, center - half)
        end = min(duration, center + half)
        candidates.append(Highlight(start, end, float(score)))

    candidates.sort(key=lambda h: h.score, reverse=True)

    selected: List[Highlight] = []
    for cand in candidates:
        if all(cand.end <= s.start or cand.start >= s.end for s in selected):
            selected.append(cand)
        if len(selected) >= top_n:
            break

    selected.sort(key=lambda h: h.start)
    return selected


def cut_clip(input_path: str, highlight: Highlight, output_path: str) -> str:
    duration = highlight.end - highlight.start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(highlight.start),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


# ==========================================
# 3. AUTO-TRANSCRIPTION (Whisper)
# ==========================================

def transcribe(input_path: str, model_size: str = "small") -> List[dict]:
    """
    Returns a list of {start, end, text} segments.
    Uses faster-whisper for speed; falls back to skipping captions
    if the library isn't installed.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[!] faster-whisper not installed — skipping captions. "
              "Run: pip install faster-whisper")
        return []

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(input_path, beam_size=5)

    out = []
    for seg in segments:
        out.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return out


def segments_to_srt(segments: List[dict], srt_path: str) -> str:
    def fmt(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text']}\n\n")
    return srt_path


# ==========================================
# 4. RENDER: burn captions + hook overlay + crop formats
# ==========================================

def render_widescreen_with_captions(
    input_path: str, srt_path: Optional[str], output_path: str, hook_text: str = ""
) -> str:
    vf_parts = []
    if hook_text:
        safe_hook = hook_text.replace(":", r"\:").replace("'", r"\'")
        vf_parts.append(
            f"drawtext=text='{safe_hook}':fontsize=48:fontcolor=white:"
            f"borderw=3:bordercolor=black:x=(w-text_w)/2:y=40"
        )
    if srt_path and os.path.exists(srt_path):
        vf_parts.append(f"subtitles={srt_path}:force_style='FontSize=20,Outline=2'")

    vf = ",".join(vf_parts) if vf_parts else None

    cmd = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def render_vertical_short(
    input_path: str, srt_path: Optional[str], output_path: str, hook_text: str = ""
) -> str:
    vf_parts = ["crop=ih*(9/16):ih", "scale=1080:1920"]
    if hook_text:
        safe_hook = hook_text.replace(":", r"\:").replace("'", r"\'")
        vf_parts.append(
            f"drawtext=text='{safe_hook}':fontsize=60:fontcolor=white:"
            f"borderw=4:bordercolor=black:x=(w-text_w)/2:y=120"
        )
    if srt_path and os.path.exists(srt_path):
        vf_parts.append(f"subtitles={srt_path}:force_style='FontSize=28,Outline=3'")

    vf = ",".join(vf_parts)
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


# ==========================================
# 5. ORCHESTRATION — stops at a review folder, does NOT auto-publish
# ==========================================

def run_smart_edit(
    source_url_or_path: str,
    hook_text: str = "You won't believe this 😱",
    review_dir: str = "review_queue",
    is_url: bool = True,
) -> List[dict]:
    """
    Runs the full transformative edit pipeline and drops finished
    renders into review_dir for human approval. Returns a list of
    dicts describing each produced clip (paths + metadata) — nothing
    here calls the YouTube upload API.
    """
    os.makedirs(review_dir, exist_ok=True)

    source_path = download_source(source_url_or_path) if is_url else source_url_or_path
    highlights = detect_highlights(source_path, clip_length=25.0, top_n=3)

    results = []
    for idx, h in enumerate(highlights):
        raw_clip = os.path.join(review_dir, f"raw_{idx}.mp4")
        cut_clip(source_path, h, raw_clip)

        segments = transcribe(raw_clip)
        srt_path = None
        if segments:
            srt_path = os.path.join(review_dir, f"captions_{idx}.srt")
            segments_to_srt(segments, srt_path)

        wide_out = os.path.join(review_dir, f"widescreen_{idx}.mp4")
        vert_out = os.path.join(review_dir, f"vertical_{idx}.mp4")
        render_widescreen_with_captions(raw_clip, srt_path, wide_out, hook_text)
        render_vertical_short(raw_clip, srt_path, vert_out, hook_text)

        results.append({
            "index": idx,
            "highlight_score": h.score,
            "start": h.start,
            "end": h.end,
            "widescreen_path": wide_out,
            "vertical_path": vert_out,
            "transcript_preview": " ".join(s["text"] for s in segments[:3]),
        })

    manifest_path = os.path.join(review_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[+] {len(results)} clip(s) ready for review in: {review_dir}")
    print(f"[+] Manifest: {manifest_path}")
    print("[+] Nothing was uploaded. Review the clips, then publish manually")
    print("    or call YouTubePublisher.upload_video() on the ones you approve.")
    return results


if __name__ == "__main__":
    # Example usage — replace with a URL you have the right to use.
    SOURCE_URL = "PUT_YOUR_OWN_OR_LICENSED_VIDEO_URL_HERE"
    run_smart_edit(SOURCE_URL, hook_text="Wait for it...")

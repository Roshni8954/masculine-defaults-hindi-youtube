import subprocess
import os
import sys
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_CSV   = r"C:\Users\roshn\OneDrive\Desktop\hindi_discourse_study\data\videos_raw.csv"
AUDIO_DIR   = r"D:\hindi_discourse_study\audio"
FFMPEG_PATH = r"C:\Users\roshn\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
MAX_WORKERS = 5
MIN_DURATION = 600  # 10 minutes

os.makedirs(AUDIO_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)

# ── fix column name: use channel_title not channel_name ───────
if "channel_name" not in df.columns and "channel_title" in df.columns:
    df["channel_name"] = df["channel_title"]

total = len(df)
print(f"Total videos : {total}")

# ── scan already downloaded files across all community folders ─
already_done = set()
for community_folder in os.listdir(AUDIO_DIR):
    folder_path = os.path.join(AUDIO_DIR, community_folder)
    if os.path.isdir(folder_path):
        for fname in os.listdir(folder_path):
            if fname.endswith(".mp3"):
                vid = fname.replace(".mp3", "").split("__")[-1]
                already_done.add(vid)

print(f"Already done : {len(already_done)}")
print(f"Remaining    : {total - len(already_done)}\n")

success_count = 0
failed_count  = 0
skipped_count = 0


def download_video(row):
    video_id     = str(row["video_id"]).strip()
    community    = str(row["community"]).strip().replace(" ", "_")
    channel_name = str(row["channel_name"]).strip().replace(" ", "_")
    duration     = row.get("duration_seconds", 0)

    # ── skip if already downloaded ─────────────────────────────
    if video_id in already_done:
        return video_id, "skipped", ""

    # ── skip if less than 10 minutes ───────────────────────────
    try:
        dur = float(duration)
        if dur < MIN_DURATION:
            return video_id, "skipped_short", f"duration {dur:.0f}s < 600s"
    except (TypeError, ValueError):
        pass

    # ── create community folder on D: drive ────────────────────
    community_dir = os.path.join(AUDIO_DIR, community)
    os.makedirs(community_dir, exist_ok=True)

    output_path = os.path.join(community_dir, f"{channel_name}__{video_id}.mp3")
    temp_path   = os.path.join(community_dir, f"__temp__{video_id}.mp3")
    url         = f"https://www.youtube.com/watch?v={video_id}"
    import time; time.sleep(1)

    # ── Stage 1: download first 10 min audio ───────────────────
    download_cmd = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--format", "bestaudio[ext=m4a]/bestaudio/best",
        "--audio-format", "mp3",
        "--audio-quality", "7",           # reduced for storage saving
        "--ffmpeg-location", FFMPEG_PATH,
        "--download-sections", "*0-600",
        "--force-keyframes-at-cuts",
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        "-o", temp_path,
        url,
    ]

    # ── Stage 2: exact hard trim to exactly 600 seconds ────────
    trim_cmd = [
        os.path.join(FFMPEG_PATH, "ffmpeg.exe"),
        "-y",
        "-i", temp_path,
        "-t", "600",
        "-c", "copy",
        "-loglevel", "error",
        output_path,
    ]

    try:
        # Stage 1 — download
        subprocess.run(
            download_cmd,
            check=True,
            timeout=600,
            capture_output=True,
            text=True,
        )

        # Stage 2 — exact trim
        subprocess.run(
            trim_cmd,
            check=True,
            timeout=60,
            capture_output=True,
            text=True,
        )

        # clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return video_id, "success", ""

    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        err = e.stderr[-300:] if e.stderr else "no error message"
        return video_id, "failed", err

    except subprocess.TimeoutExpired:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return video_id, "timeout", ""


# ── run parallel downloads ─────────────────────────────────────
rows = [row for _, row in df.iterrows()]

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(download_video, row): row for row in rows}

    done = 0
    for future in as_completed(futures):
        video_id, status, reason = future.result()
        done += 1

        if status == "success":
            success_count += 1
            print(f"[{done}/{total}] ✅ OK      : {video_id}")

        elif status == "skipped":
            skipped_count += 1
            print(f"[{done}/{total}] ⏭  SKIP    : {video_id} (already downloaded)")

        elif status == "skipped_short":
            skipped_count += 1
            print(f"[{done}/{total}] ⏭  SKIP    : {video_id} ({reason})")

        elif status == "failed":
            failed_count += 1
            print(f"[{done}/{total}] ❌ FAILED  : {video_id}")
            if reason:
                print(f"    REASON : {reason}")

        elif status == "timeout":
            failed_count += 1
            print(f"[{done}/{total}] ⏱  TIMEOUT : {video_id}")

        # progress every 50 videos
        if done % 50 == 0:
            print(f"\n--- Progress: ✅{success_count} done  ❌{failed_count} failed  ⏭{skipped_count} skipped ---\n")

print(f"\n{'='*50}")
print(f"DOWNLOAD COMPLETE")
print(f"{'='*50}")
print(f"✅ Downloaded : {success_count}")
print(f"⏭  Skipped    : {skipped_count}")
print(f"❌ Failed     : {failed_count}")
print(f"📁 Audio in   : {AUDIO_DIR}")
# ============================================================
# FILE 4: Gender Detection using inaSpeechSegmenter
# Input:  D:/hindi_discourse_study/audio/community/channel__videoID.mp3
# Output: data/gender_results.csv
#         Summary per community printed at end
# ============================================================

import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# ── PATHS ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
AUDIO_DIR  = Path(r"D:\hindi_discourse_study\audio")
OUTPUT_CSV = BASE_DIR / "data" / "gender_results.csv"

os.makedirs(OUTPUT_CSV.parent, exist_ok=True)

# ── LOAD inaSpeechSegmenter ───────────────────────────────────
print("Loading inaSpeechSegmenter model...")
from inaSpeechSegmenter import Segmenter
seg = Segmenter()
print("Model loaded!\n")

# ── LOAD EXISTING RESULTS (resume support) ────────────────────
if OUTPUT_CSV.exists():
    existing_df  = pd.read_csv(OUTPUT_CSV)
    already_done = set(existing_df["video_id"].tolist())
    print(f"Already processed : {len(already_done)} videos")
else:
    existing_df  = pd.DataFrame()
    already_done = set()
    print("Starting fresh gender detection")

# ── COLLECT ALL AUDIO FILES ───────────────────────────────────
audio_files = []

for community_folder in os.listdir(AUDIO_DIR):
    folder_path = AUDIO_DIR / community_folder
    if not folder_path.is_dir():
        continue

    for fname in os.listdir(folder_path):
        if not fname.endswith(".mp3"):
            continue

        # filename = channelname__videoID.mp3
        parts    = fname.replace(".mp3", "").split("__")
        video_id = parts[-1]
        channel  = parts[0] if len(parts) >= 2 else "unknown"

        audio_files.append({
            "path":      folder_path / fname,
            "video_id":  video_id,
            "channel":   channel,
            "community": community_folder,
            "filename":  fname,
        })

total     = len(audio_files)
remaining = total - len(already_done)
print(f"Total audio files : {total}")
print(f"Remaining         : {remaining}\n")

# ── RUN GENDER DETECTION ──────────────────────────────────────
results  = []
success  = 0
failed   = 0
skipped  = 0

for item in tqdm(audio_files, desc="Detecting gender"):
    video_id  = item["video_id"]
    channel   = item["channel"]
    community = item["community"]
    audio_path= item["path"]

    # skip already processed
    if video_id in already_done:
        skipped += 1
        continue

    try:
        # run gender segmentation
        segmentation = seg(str(audio_path))

        male_seconds   = 0.0
        female_seconds = 0.0
        music_seconds  = 0.0
        noise_seconds  = 0.0

        for label, start, end in segmentation:
            duration = end - start
            if label == "male":
                male_seconds   += duration
            elif label == "female":
                female_seconds += duration
            elif label == "music":
                music_seconds  += duration
            elif label in ("noise", "noEnergy"):
                noise_seconds  += duration

        total_speech = male_seconds + female_seconds
        male_pct     = (male_seconds   / total_speech * 100) if total_speech > 0 else 0
        female_pct   = (female_seconds / total_speech * 100) if total_speech > 0 else 0

        # dominant gender
        if male_seconds > female_seconds:
            dominant_gender = "male"
        elif female_seconds > male_seconds:
            dominant_gender = "female"
        else:
            dominant_gender = "unknown"

        results.append({
            "video_id":        video_id,
            "channel":         channel,
            "community":       community,
            "filename":        item["filename"],
            "male_seconds":    round(male_seconds,   2),
            "female_seconds":  round(female_seconds, 2),
            "music_seconds":   round(music_seconds,  2),
            "noise_seconds":   round(noise_seconds,  2),
            "male_pct":        round(male_pct,        2),
            "female_pct":      round(female_pct,      2),
            "dominant_gender": dominant_gender,
        })
        success += 1

        # save every 50 videos to protect progress
        if success % 50 == 0:
            save_df  = pd.DataFrame(results)
            final_df = pd.concat([existing_df, save_df], ignore_index=True)
            final_df.to_csv(OUTPUT_CSV, index=False)
            print(f"\n  Progress saved: {len(final_df)} total processed")

    except Exception as e:
        print(f"\nError on {video_id}: {e}")
        failed += 1

# ── FINAL SAVE ────────────────────────────────────────────────
if results:
    new_df   = pd.DataFrame(results)
    final_df = pd.concat([existing_df, new_df], ignore_index=True)
    final_df.to_csv(OUTPUT_CSV, index=False)
else:
    final_df = existing_df

# ── SUMMARY ──────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"GENDER DETECTION COMPLETE")
print(f"{'='*55}")
print(f"Successfully processed : {success}")
print(f"Skipped (already done) : {skipped}")
print(f"Failed                 : {failed}")
print(f"Total in CSV           : {len(final_df)}")
print(f"Saved to               : {OUTPUT_CSV}")

print(f"\n{'='*55}")
print(f"SUMMARY BY COMMUNITY")
print(f"{'='*55}")
for community in final_df["community"].unique():
    comm_df        = final_df[final_df["community"] == community]
    male_count     = len(comm_df[comm_df["dominant_gender"] == "male"])
    female_count   = len(comm_df[comm_df["dominant_gender"] == "female"])
    unknown_count  = len(comm_df[comm_df["dominant_gender"] == "unknown"])
    avg_male_pct   = comm_df["male_pct"].mean()
    avg_female_pct = comm_df["female_pct"].mean()
    print(f"\n  {community}")
    print(f"    Total videos     : {len(comm_df)}")
    print(f"    Male dominant    : {male_count}")
    print(f"    Female dominant  : {female_count}")
    print(f"    Unknown          : {unknown_count}")
    print(f"    Avg male %       : {avg_male_pct:.1f}%")
    print(f"    Avg female %     : {avg_female_pct:.1f}%")

print(f"\n{'='*55}")
print(f"SUMMARY BY CHANNEL")
print(f"{'='*55}")
channel_summary = final_df.groupby("channel").agg(
    videos=("video_id", "count"),
    avg_male_pct=("male_pct", "mean"),
    avg_female_pct=("female_pct", "mean"),
    dominant=("dominant_gender", lambda x: x.value_counts().index[0])
).reset_index()
print(channel_summary.to_string(index=False))
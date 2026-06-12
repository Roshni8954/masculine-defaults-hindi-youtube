# ============================================================
# FILE 3: Transcribe Hindi audio using Whisper
# Input:  audio/community/channel__videoID.mp3
# Output: data/transcripts.json
# ============================================================

import whisper
import os
import json
from pathlib import Path
from tqdm import tqdm

BASE_DIR     = Path(__file__).resolve().parent
AUDIO_DIR    = BASE_DIR / "audio"
OUTPUT_FILE  = BASE_DIR / "data" / "transcripts.json"
WHISPER_MODEL = "small"   # good balance for Hindi on CPU

os.makedirs(OUTPUT_FILE.parent, exist_ok=True)

# ── load existing transcripts (resume support) ─────────────────
if OUTPUT_FILE.exists():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        transcripts = json.load(f)
    print(f"Resuming — already transcribed: {len(transcripts)}")
else:
    transcripts = {}
    print("Starting fresh transcription")

# ── load Whisper model ──────────────────────────────────────────
print(f"\nLoading Whisper '{WHISPER_MODEL}' model...")
print("First run downloads ~460MB — please wait\n")
model = whisper.load_model(WHISPER_MODEL)
print("Model loaded!\n")

# ── collect all audio files across community folders ───────────
audio_files = []
for community_folder in os.listdir(AUDIO_DIR):
    folder_path = AUDIO_DIR / community_folder
    if folder_path.is_dir():
        for fname in os.listdir(folder_path):
            if fname.endswith(".mp3"):
                # filename = channelname__videoID.mp3
                video_id = fname.replace(".mp3", "").split("__")[-1]
                channel  = fname.replace(".mp3", "").split("__")[0]
                audio_files.append({
                    "path":      folder_path / fname,
                    "video_id":  video_id,
                    "community": community_folder,
                    "channel":   channel,
                })

total = len(audio_files)
remaining = total - len(transcripts)
print(f"Total audio files : {total}")
print(f"Already done      : {len(transcripts)}")
print(f"Remaining         : {remaining}\n")

# ── transcribe ────────────────────────────────────────────────
success = 0
failed  = 0

for item in tqdm(audio_files, desc="Transcribing"):
    video_id = item["video_id"]

    # skip if already transcribed
    if video_id in transcripts:
        continue

    audio_path = item["path"]

    try:
        result = model.transcribe(
            str(audio_path),
            language="hi",       # Hindi
            task="transcribe",   # not translate
            fp16=False           # required for CPU
        )

        transcripts[video_id] = {
            "text":      result["text"],
            "community": item["community"],
            "channel":   item["channel"],
        }
        success += 1

        # save after every video — protects progress
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(transcripts, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"\nError on {video_id}: {e}")
        failed += 1

# ── summary ──────────────────────────────────────────────────
print(f"\n{'='*50}")
print("TRANSCRIPTION COMPLETE")
print(f"{'='*50}")
print(f"Successfully transcribed : {success}")
print(f"Failed                   : {failed}")
print(f"Total in file            : {len(transcripts)}")
print(f"Saved to                 : {OUTPUT_FILE}")
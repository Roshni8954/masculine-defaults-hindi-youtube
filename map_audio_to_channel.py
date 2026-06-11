import os
import re
import pandas as pd

AUDIO_DIR = "audio"
INPUT_CSV = "data/videos_raw.csv"
OUTPUT_CSV = "results/audio_mapping.csv"


def load_metadata(csv_path):
    df = pd.read_csv(csv_path, dtype=str)
    df = df.fillna("")
    mapping = {}
    for _, r in df.iterrows():
        vid = str(r.get("video_id", "")).strip()
        if not vid:
            continue
        community = str(r.get("community", "")).strip()
        channel = str(r.get("channel_name", "")).strip()
        mapping[vid] = {"community": community, "channel_name": channel}
    return mapping


def extract_video_id(filename):
    name = os.path.splitext(filename)[0]
    # common pattern: community__channel__<videoid>
    parts = name.split("__")
    if parts and re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[-1]):
        return parts[-1]

    # else try to find a trailing 11-char id
    m = re.search(r"([A-Za-z0-9_-]{11})$", name)
    if m:
        return m.group(1)

    # fallback: if filename itself is 11 chars
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", name):
        return name

    return None


def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    meta = load_metadata(INPUT_CSV)

    rows = []
    mapped = 0
    unmapped = 0
    for fname in sorted(os.listdir(AUDIO_DIR)):
        if fname.startswith("."):
            continue
        fpath = os.path.join(AUDIO_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        vid = extract_video_id(fname)
        community = ""
        channel = ""
        if vid and vid in meta:
            community = meta[vid]["community"]
            channel = meta[vid]["channel_name"]
            mapped += 1
        else:
            unmapped += 1

        rows.append({"audio_file": fname, "video_id": vid or "", "community": community, "channel_name": channel})

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Mapped: {mapped}, Unmapped: {unmapped}, Total: {len(rows)}")
    print(f"Wrote mapping to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

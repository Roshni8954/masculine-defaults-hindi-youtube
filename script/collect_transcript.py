import pandas as pd
import os
from tqdm import tqdm


# IMPORT TRANSCRIPT API

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)


# LOAD CSV

videos = pd.read_csv(
    "data/metadata/all_videos.csv"
)

# CREATE OUTPUT FOLDER

os.makedirs(
    "data/transcripts",
    exist_ok=True
)

success = 0
failed = 0

# CREATE API OBJECT

ytt_api = YouTubeTranscriptApi()

# PROCESS VIDEOS

for _, row in tqdm(
        videos.iterrows(),
        total=len(videos),
        desc="Transcripts"):

    video_id = str(row["video_id"]).strip()

    community = str(
        row["community"]
    ).strip()

    community_folder = os.path.join(
        "data",
        "transcripts",
        community
    )

    os.makedirs(
        community_folder,
        exist_ok=True
    )

    save_file = os.path.join(
        community_folder,
        f"{video_id}.txt"
    )

    # skip already saved
    if os.path.exists(save_file):
        success += 1
        continue

    try:

        # FETCH TRANSCRIPT

        transcript = ytt_api.fetch(
            video_id
        )

        text_parts = []

        for segment in transcript:

            if segment.start < 600:
                text_parts.append(
                    segment.text
                )

        final_text = " ".join(
            text_parts
        )

        if len(final_text.strip()) == 0:
            failed += 1
            continue

        with open(
            save_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(final_text)

        success += 1

    except (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable
    ) as e:

        failed += 1

        print(
            f"\nFailed: {video_id}"
        )

        print(
            f"Reason: {type(e).__name__}"
        )

    except Exception as e:

        failed += 1

        print(
            f"\nFailed: {video_id}"
        )

        print(
            f"Reason: {str(e)}"
        )

# SUMMARY

print("\n")
print("=" * 50)
print("TRANSCRIPT EXTRACTION COMPLETE")
print("=" * 50)
print(f"Successful : {success}")
print(f"Failed     : {failed}")
print("=" * 50)
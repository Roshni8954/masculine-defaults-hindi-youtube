from googleapiclient.discovery import build
import pandas as pd
from isodate import parse_duration
from tqdm import tqdm
import os
import time


API_KEY = "AIzaSyCumet7OqJMRHO3n45DURBfb5_VKiF4-vg"

VIDEOS_PER_CHANNEL = 85
MIN_DURATION_SECONDS = 600  # 10 minutes

# YOUTUBE CLIENT

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# READ CHANNEL LIST

channels = pd.read_csv(
    "config/channels.csv"
)

all_videos = []


# GET VIDEO DURATION

def get_video_duration(video_id):

    try:

        request = youtube.videos().list(
            part="contentDetails",
            id=video_id
        )

        response = request.execute()

        items = response.get("items", [])

        if not items:
            return None

        duration = items[0][
            "contentDetails"
        ]["duration"]

        seconds = int(
            parse_duration(duration)
            .total_seconds()
        )

        return seconds

    except Exception as e:

        print(
            f"Duration error: {video_id}"
        )

        return None

# COLLECT CHANNEL VIDEOS

for _, row in tqdm(
        channels.iterrows(),
        total=len(channels),
        desc="Channels"):

    channel_id = row["channel_id"]

    channel_name = row["channel_name"]

    community = row["community"]

    gender = row["gender"]

    print(
        f"\nCollecting: {channel_name}"
    )

    next_page = None

    qualifying_videos = 0

    while qualifying_videos < VIDEOS_PER_CHANNEL:

        try:

            request = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                order="date",
                type="video",
                maxResults=50,
                pageToken=next_page
            )

            response = request.execute()

            items = response.get(
                "items",
                []
            )

            if not items:
                break

            for item in items:

                if qualifying_videos >= VIDEOS_PER_CHANNEL:
                    break

                try:

                    video_id = item[
                        "id"
                    ]["videoId"]

                    duration = get_video_duration(
                        video_id
                    )

                    # skip if duration unavailable
                    if duration is None:
                        continue

                    # skip videos shorter than 10 mins
                    if duration < MIN_DURATION_SECONDS:
                        continue

                    all_videos.append({

                        "community":
                            community,

                        "channel_name":
                            channel_name,

                        "gender":
                            gender,

                        "channel_id":
                            channel_id,

                        "video_id":
                            video_id,

                        "title":
                            item["snippet"]["title"],

                        "published":
                            item["snippet"][
                                "publishedAt"
                            ],

                        "duration_seconds":
                            duration
                    })

                    qualifying_videos += 1

                    print(
                        f"  {qualifying_videos}/85",
                        end="\r"
                    )

                except Exception:
                    continue

            next_page = response.get(
                "nextPageToken"
            )

            if not next_page:
                break

        except Exception as e:

            print(
                f"\nChannel Error: "
                f"{channel_name}"
            )

            print(e)

            break

        time.sleep(0.1)


# SAVE OUTPUT

os.makedirs(
    "data/metadata",
    exist_ok=True
)

df = pd.DataFrame(all_videos)

df.to_csv(
    "data/metadata/all_videos.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n")
print("=" * 40)
print("COLLECTION COMPLETE")
print("=" * 40)
print(
    f"Total videos collected: "
    f"{len(df)}"
)
print(
    "Saved to "
    "../data/metadata/all_videos.csv"
)
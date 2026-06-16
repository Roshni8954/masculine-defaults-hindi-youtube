# ============================================================
# FILE 1: Collect videos using UPLOADS PLAYLIST method
# - Latest 85 videos per channel (≥ 10 minutes only)
# - Skips videos already in videos_raw.csv
# - Sorted by newest first
# Output: data/videos_raw.csv
# ============================================================

from googleapiclient.discovery import build
import pandas as pd
import time
import os
import isodate

with open("api_key.txt", "r") as f:
    API_KEY = f.read().strip()

VIDEOS_PER_CHANNEL = 90
MIN_DURATION       = 600   # 10 minutes in seconds
OUTPUT_CSV         = "data/videos_raw.csv"

# ── ALL COMMUNITIES AND CHANNELS ─────────────────────────────
communities = {
    "religion_spirituality": [
        ("UCcYzLCs3zrQIBVHYA1sK2sw", "Sadhguru"),
        ("UCclfz6zVWWOpsQsg3OheI3g", "SwamiMukundananda"),
        ("UCEk1jBxAl6fe-_G37G7huQA", "BhajanMarg"),
        ("UCDe0DwkMVFfSIoiYdQUPQmQ", "Aniruddhacharyaji"),
        ("UCIqPPQgDbb7Ud-zqGOP8TAw", "Chitralekhaji"),
        ("UCsW4PL6aOwAZ7784hAsLJOQ", "AnkitSajwanMinistries"),
        ("UCCaslSGCxW7FyeJ2kkYkP0g", "ShibuThomasOfficial"),
        ("UC6BnmdAkOs2delp7bUmPzBA", "MohanCLazarus"),
        ("UCn6UW4xEVwjzd2y0Vz58uHA", "GurudevHindi"),
        ("UCczZnI6hkhkdvEPwUrQVMcQ", "DrZakirNaik"),
        ("UCC3pnIpWMVail5J8mvYEiZA", "MuftiTariqMasood"),
        ("UCqjTcfF_oH3h4hytq7TREMQ", "IslamKnowledgeOnly"),
        ("UCjnYFKdyUxymRVCNa2lPTog", "JaiJinendra"),
        ("UCsQUid3uu0yB2SLGq88EkHg", "Terapanth"),
        ("UCAI4HhRMcBycUuKhk0TUVQw", "BuddhaBroadCast"),
        ("UCbsVNxLVgkSRCYs49xa8W0w", "AnandmurtiGurumaa"),
    ],
    "tech_coding": [
        ("UCkGS_3D0HEzfflFnG0bD24A", "MySirG"),
        ("UCY6N8zZhs2V7gNTUxPuKWoQ", "IshanSharma"),
        ("UCBwmMxybNva6P_5VmxjzwqA", "ApnaCollege"),
        ("UCeVMnSShP_Iviwkknt83cww", "CodeWithHarry"),
        ("UCdp6GUwjKscp5ST4M4WgIpw", "TechWiser"),
        ("UCEPL07qzVsOcHd3sMUws65g", "TrakinTech"),
        ("UCOhHO2ICt0ti9KAh-QHvttQ", "TechnicalGuruji"),
        ("UCIP8eTZKqygyeZ9UtB6rsWw", "CodeStudioByPrachi"),
        ("UC8rR-i29Io48fD3bDd0paZw", "SaumyaSingh"),
        ("UC6KENAB_qBg-UzqVYHhshvQ", "AECComputers"),
        ("UCM-yUTYGmrNvKOCcAl21g3w", "JennyslecturesCSIT"),
        ("UCDrf0V4fcBr5FlCtKwvpfwA", "CollegeWallahbyPWSkills"),
        ("UC1tVU8H153ZFO9eRsxdJlhA", "TechnologyGyan"),
        ("UCA6yfpYhy5sWMjRGOT-OAIQ", "KNOWLEDGEGATE"),
        ("UCJskGeByzRRSvmOyZOz61ig", "takeUforward"),
        ("UCldyi11QYNXYXiLjVbyw5dA", "CodeHelp"),
    ],
    "business_finance": [
        ("UCRzYN32xtBf3Yxsx5BvJWJw", "Warikoo"),
        ("UCe3qdG0A_gr-sEdat5y2twQ", "CARachanaRanade"),
        ("UCwAdQUuPT6laN-AQR17fe1g", "PranjalKamra"),
        ("UCwVEhEzsjLym_u1he4XWFkg", "FinanceWithSharan"),
        ("UCzUgCORf79EjqlNHmGRHFkA", "NehaNagar"),
        ("UCVOTBwF0vnSxMRIbfSE_K_g", "LabourLawAdvisor"),
        ("UCQpPo9BNwezg54N9hMFQp6Q", "nischa/featured"),
        ("UCEAAzv2OBqxsSczKJ2QZyGQ", "PushkarRajThakurOfficial"),
        ("UCvqttS8EzhRq2YWg03qKRCQ", "Sanjay_Kathuria"),
        ("UCzUgCORf79EjqlNHmGRHFkA", "FinancialFreedom"),
        ("UCdvOCtR3a9ICLAw0DD3DpXg", "bekifaayati"),
        ("UCqW8jxh4tH1Z1sWPbkGWL4g", "AkshatZayn"),
    ],
    "lifestyle_vlogs": [
        ("UCjvgGbPPn-FgYeguc5nxG4A", "SouravJoshiVlogs"),
        ("UCDnq05Q89oYq-Tz5boL73Tw", "CurlyTales"),
        ("UCozheH90vpNCOU15VgUgvog", "KritikaThatBohoGirl"),
        ("UCHDQOZjxuSm0-LgLQtMeCqw", "DimpleMalhanVlogs"),
        ("UCWrIczmOFMmQ2wxWZpvKrPQ", "SmithaDepak"),
        ("UCNn6AaHharXIbkRleXGboiQ", "MumbikerNikhil"),
        ("UCVaSUu1B_Y4R2rFLUpvRmlA", "TheFormalEdit"),
        ("UCD8CFS_nj2_dBdSZu53wCcQ", "KritikaGoel"),
        ("UCt4pGsEsc_TDXDx0iRStdCg", "JannatZubair"),
        ("UCiKNX0TIMyKgGqQznhR1Xig", "LifeOfLimbachiyaas"),
        ("UCn8Fiasqd-6G3A6AS322mZA", "FitMuscleTV"),
        ("UCBryxYkuBwLWCv9Yuws-0Dw", "YasminBodyImage"),
        ("UCGeGhS_akOxBWQcSmje6B-w", "TanyaKhanijow"),
    ],
    "politics_news": [
        ("UC-CSyyi47VX1lD9zyeABW3w", "DhruvRathee"),
        ("UCz4a7agVFr1TxU-mpAP8hkw", "MohakMangal"),
        ("UCOtQWL2z-tFbI-mgy_Rpdgg", "UnfilteredBySamdish"),
        ("UCnC8SAZzQiBGYVSKZ_S3y4Q", "NikhilKamath"),
        ("UC0yXUUIaPVAqZLgRjvtMftw", "RavishKumar"),
        ("UC1bUswUinAEFYaRQFvAKjPA", "ChanakyadialogsHindi"),
        ("UCsDTy8jvHcwMvSZf_JGi-FA", "AbhiAndNiyu"),
        ("UC5n-0ihUiOuuvZSSUnMNZLw", "NikitaKThakur"),
        ("UCatL-c6pmnjzEOHSyjn-sHA", "KhangsResearchCentre"),
        ("UC3-IDKNIABI98_J2aqa2YjQ", "ThinkSchoolHindi"),
        ("UCR-foyF-C6VuAlwy3KZMkgA", "MrVivekBindra"),
        ("UCzI8K9xO_5E-4iCP7Km6cRQ", "FayeDSouza"),
        ("UCfnoKx2jyLdoQoSBa6XvvUA", "TheSwaddleTV"),
        ("UCmTM_hPCeckqN3cPWtYZZcg", "thedeshbhakt"),
        ("UCrdPiSPVW0rtRsI002BX8iw", "mojostory"),
        ("UCcqiFa0iQxVD_CDSe-dHXGA", "SupriyaShrinate"),
    ],
    "self_help": [
        ("UCzwCEE_PchiBULMnAJqhGVg", "RajShamani"),
        ("UCBqFKDipsnzvJdt6UT0lMIg", "SandeepSeminars"),
        ("UCz22l7kbce-uFJAoaZqxD1A", "GaurGopalDas"),
        ("UCQdyCrZpGq4Bbu6V8LPUDWg", "bkshivani"),
        ("UCxe5Nq5v4jFYhwkDQDIFo2w", "AdeteDahiya"),
        ("UCD3vQ2YqC_sxUJ2OikLYjGQ", "nishkarshsharmaa"),
        ("UC3xNlZYxWt6fys0G6uubprQ", "dr.tanujain9500"),
        ("UCFqZv-Oo8u8V7QEzVqOBCgQ", "PriyaKumarMotivationalSpeaker"),
        ("UCqXCX2DnQZh8e4VNT7MPTtA", "UjjwalPatni"),
        ("UC1gDWPG73kPaiTdat8ypvAA", "DeepakDaiya"),

    ],
    "gaming_esports": [
        ("UC5c9VlYTSvBSCaoMu_GI6gQ", "TotalGaming"),
        ("UCX8pnu3DYUnx8qy8V_c6oHg", "TechnoGamerzOfficial"),
        ("UCMrvxKTx9hLhZcOvJkYOnAw", "ASGaming"),
        ("UC0IWRLai-BAwci_e9MylNGw", "CarryisLive"),
        ("UCFwKgzKe-EdTz83r6wzhmOw", "LiveInsaan"),
        ("UCF1KpKu_VDjDgIThFQJqYkw", "GodLikeEsports"),
        ("UCv-iyxr1zXiqqfKf0ROT-bg", "GoldyHindiGaming"),
        ("UCYFnBsDPU_lMGlmOY8dLcjQ", "TeamVitalityIndia"),
        ("UCUm7FZcnD_4n0S4btbHL1HQ", "OrangutanTV"),
        ("UC6GIR5W1Bm5Moc3kzKV-nhw", "KrutikaPlays"),
        ("UCwA3yPBSbZpwse6Q0aA2LPg", "PayalGaming"),
        ("UCcz2rzroRCKuR0pi6Oj-SbQ", "MilikyaMili"),
        ("UCqQfK7YxUCmIWu4hl_Qv74g", "XyaaLive"),
        ("UCH4YXG1SMJQsbG8T8gK42Lg", "AnkkitaC"),
        ("UCdQPeeJ0qGK6wWBiEJWcdsQ", "LokeshGamer"),
    ],
    "standup_comedy": [
        ("UCNqA44cRILQDwm9MG0vV-Og", "RahulDua"),
        ("UCVmEbEQUGXHVm-O9pqa3JWg", "TheHarshBeniwal"),
        ("UCt4atlExw8aj3Bm79nv1fig", "Round2hell"),
        ("UC7IMq6lLHbptAnSucW1pClA", "FilterCopy"),
        ("UC7eHZXheF8nVOfwB2PEslMw", "ashishchanchlanivines"),
        ("UCaUr7y4F9lWGnZ0cbUZyzYA", "ashishsolanki"),
        ("UCeP5_FL11TnvXuvrFvALJyA", "GauravKapoor"),
        ("UCfLuT3JwLx8rvHjHfTymekw", "triggeredinsaan"),
        ("UCx6F-rETGiz7xf_vkMmX2yQ", "Mythpat"),
        ("UCdxbhKxr8pyWTx1ExCSmJRw", "Girliyapa"),
        ("UClJc-8Isx8-vD8tMZkGGDpg", "madhurvirliraw"),
        ("UCqzcceB6MQJZ5L1xAu_jHiQ", "VivekSamtan"),
        ("UCtgGOdTlM-NdJ9rPKIYN8UQ", "SlayyPointOfficial"),
        ("UC0rE2qq81of4fojo-KhO5rg", "tanmaybhat"),
        ("UC6xOVUMstTf08rUgOFbyPEA", "SNGComedy"),
        ("UCYLS9TSah19IsB8yyUpiDzg", "Jordindian"),
        ("UCy9cb7U-Asbhbum0ZXArvfQ", "HiSaimanSay"),
        ("UCvlgR3RnY_JncmU7aeI4sjQ", "devikagupta029"),
    ],
}

# ── LOAD ALREADY FETCHED VIDEO IDs ───────────────────────────
already_fetched = set()
if os.path.exists(OUTPUT_CSV):
    existing_df     = pd.read_csv(OUTPUT_CSV)
    already_fetched = set(existing_df["video_id"].tolist())
    print(f"Already fetched : {len(already_fetched)} videos")
else:
    existing_df = pd.DataFrame()
    print("No existing CSV found — starting fresh")

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_uploads_playlist_id(channel_id):
    return "UU" + channel_id[2:]

def parse_duration(duration_str):
    try:
        return int(isodate.parse_duration(duration_str).total_seconds())
    except:
        return 0

def get_video_details(video_ids):
    """Get duration for a batch of video IDs — 50 at a time"""
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            request = youtube.videos().list(
                part="contentDetails",
                id=",".join(batch)
            )
            response = request.execute()
            for item in response.get("items", []):
                vid_id   = item["id"]
                duration = item["contentDetails"]["duration"]
                details[vid_id] = parse_duration(duration)
        except Exception as e:
            print(f"  Error fetching durations: {e}")
        time.sleep(0.2)
    return details

def get_latest_videos(playlist_id, channel_name, needed=85):
    """
    Fetch latest videos from uploads playlist.
    Keeps fetching pages until we have 'needed' valid videos
    (>= 10 min and not already fetched).
    Videos come newest first from uploads playlist.
    """
    collected       = []
    next_page_token = None
    page            = 0

    while len(collected) < needed:
        page += 1
        try:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            items    = response.get("items", [])

            if not items:
                break

            # collect video IDs from this page
            page_videos = []
            for item in items:
                snippet  = item["snippet"]
                video_id = snippet["resourceId"]["videoId"]

                # skip already fetched
                if video_id in already_fetched:
                    continue

                page_videos.append({
                    "video_id":      video_id,
                    "title":         snippet["title"],
                    "published_at":  snippet["publishedAt"],
                    "channel_id":    snippet["channelId"],
                    "channel_title": channel_name,
                })

            # get durations for this page batch
            page_ids  = [v["video_id"] for v in page_videos]
            durations = get_video_details(page_ids)

            # keep only videos >= 10 minutes
            for v in page_videos:
                dur = durations.get(v["video_id"], 0)
                v["duration_seconds"] = dur
                if dur >= MIN_DURATION:
                    collected.append(v)
                    if len(collected) >= needed:
                        break

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break  # no more pages

        except Exception as e:
            print(f"  ERROR on page {page}: {e}")
            break

        time.sleep(0.3)

    return collected[:needed]


# ── RUN COLLECTION ────────────────────────────────────────────
print("\n" + "=" * 60)
print("STARTING VIDEO COLLECTION")
print("=" * 60)
print(f"Target        : {VIDEOS_PER_CHANNEL} videos per channel")
print(f"Min duration  : {MIN_DURATION}s (10 minutes)")
print(f"Skip existing : Yes\n")

new_videos = []

for community, channels in communities.items():
    print(f"\nCommunity: {community}")
    print("-" * 50)

    for channel_id, channel_name in channels:
        playlist_id = get_uploads_playlist_id(channel_id)

        print(f"  Fetching : {channel_name}...")
        videos = get_latest_videos(
            playlist_id,
            channel_name,
            needed=VIDEOS_PER_CHANNEL
        )

        for v in videos:
            v["community"] = community

        new_videos.extend(videos)
        print(f"  Collected: {len(videos)} new videos (≥10 min, not already fetched)")

# ── MERGE WITH EXISTING AND SAVE ──────────────────────────────
new_df = pd.DataFrame(new_videos)

if not new_df.empty:
    # combine old + new
    final_df = pd.concat([existing_df, new_df], ignore_index=True)
    final_df = final_df.drop_duplicates(subset=["video_id"])

    # exact column order
    final_df = final_df[[
        "video_id",
        "title",
        "published_at",
        "channel_id",
        "channel_title",
        "duration_seconds",
        "community"
    ]]

    final_df.to_csv(OUTPUT_CSV, index=False)

    print(f"\n{'='*60}")
    print(f"COLLECTION COMPLETE")
    print(f"{'='*60}")
    print(f"New videos added       : {len(new_df)}")
    print(f"Total in CSV           : {len(final_df)}")
    print(f"\nBreakdown by community:")
    print(final_df["community"].value_counts().to_string())
    print(f"\nBreakdown by channel:")
    print(final_df["channel_title"].value_counts().to_string())
    print(f"\nSaved to: {OUTPUT_CSV}")

else:
    print("\nNo new videos found — everything already fetched!")

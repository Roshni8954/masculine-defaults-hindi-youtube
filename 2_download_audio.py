import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "data" / "videos_raw.csv"
AUDIO_DIR = BASE_DIR / "audio"
RESULTS_DIR = BASE_DIR / "results"
AUTH_REQUIRED_CSV = RESULTS_DIR / "auth_required_videos.csv"
DEFAULT_FFMPEG_DIR = Path(
    r"C:\Users\roshn\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin")
MAX_WORKERS = int(os.environ.get("YTDLP_MAX_WORKERS", "10"))
MIN_DURATION = 600  # 10 minutes
REQUEST_DELAY_SECONDS = float(os.environ.get("YTDLP_REQUEST_DELAY_SECONDS", "0"))
AUTH_RETRY_WAIT = 20
DOWNLOAD_TIMEOUT = int(os.environ.get("YTDLP_DOWNLOAD_TIMEOUT", "420"))
FRAGMENT_CONCURRENCY = int(os.environ.get("YTDLP_CONCURRENT_FRAGMENTS", "4"))
BROWSER_COOKIE_CANDIDATES = ["edge", "chrome", "firefox"]
COOKIE_FILE = os.environ.get("YTDLP_COOKIE_FILE", "").strip()
YOUTUBE_EXTRACTOR_ARGS = os.environ.get(
    "YTDLP_YOUTUBE_EXTRACTOR_ARGS", "youtube:player_client=tv,mweb"
).strip()
DEFAULT_COOKIE_FILE_CANDIDATES = [
    BASE_DIR / "youtube_cookies.txt",
    BASE_DIR / "cookies.txt",
    BASE_DIR / "data" / "youtube_cookies.txt",
    BASE_DIR / "data" / "cookies.txt",
]

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

if not INPUT_CSV.exists():
    raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")


def resolve_ffmpeg_dir():
    if DEFAULT_FFMPEG_DIR.exists():
        return DEFAULT_FFMPEG_DIR

    ffmpeg_on_path = shutil.which("ffmpeg")
    if ffmpeg_on_path:
        return Path(ffmpeg_on_path).resolve().parent

    raise FileNotFoundError(
        "ffmpeg not found. Install ffmpeg or update DEFAULT_FFMPEG_DIR."
    )


def get_available_cookie_browsers():
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    browser_paths = {
        "edge": os.path.join(local, "Microsoft", "Edge", "User Data"),
        "chrome": os.path.join(local, "Google", "Chrome", "User Data"),
        "firefox": os.path.join(appdata, "Mozilla", "Firefox"),
    }

    return [
        browser
        for browser in BROWSER_COOKIE_CANDIDATES
        if os.path.exists(browser_paths[browser])
    ]


def get_configured_cookie_browsers():
    """
    Control cookie usage with YTDLP_COOKIE_MODE:
    - auto: try detected browsers, then no cookies
    - none: never use browser cookies
    - edge/chrome/firefox: only try that browser, then no cookies
    """
    mode = os.environ.get("YTDLP_COOKIE_MODE", "none").strip().lower()
    available = get_available_cookie_browsers()

    if mode in {"", "none", "off", "false", "0"}:
        return []
    if mode == "auto":
        return available
    if mode in BROWSER_COOKIE_CANDIDATES:
        return [mode] if mode in available else []

    print(
        f"Warning: unsupported YTDLP_COOKIE_MODE={mode!r}. "
        "Falling back to no browser cookies."
    )
    return []


def resolve_cookie_file():
    if not COOKIE_FILE:
        for candidate in DEFAULT_COOKIE_FILE_CANDIDATES:
            if candidate.exists():
                return candidate
        return None

    cookie_path = Path(COOKIE_FILE).expanduser()
    if not cookie_path.is_absolute():
        cookie_path = (BASE_DIR / cookie_path).resolve()

    if not cookie_path.exists():
        raise FileNotFoundError(f"Cookie file not found: {cookie_path}")

    return cookie_path


def build_download_cmd(
    url,
    output_path,
    ffmpeg_dir,
    cookie_browser=None,
    cookie_file=None,
    extractor_args=None,
):
    download_cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "-x",
        "--format",
        "bestaudio/best",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "7",
        "--ffmpeg-location",
        str(ffmpeg_dir),
        "--download-sections",
        "*0-600",
        "--no-playlist",
        "--retries",
        "3",
        "--fragment-retries",
        "3",
        "--concurrent-fragments",
        str(FRAGMENT_CONCURRENCY),
        "--quiet",
       "--no-warnings",
       "--remote-components", "ejs:github",
       "-o",
       output_path,
       url,
    ]
    if extractor_args:
        download_cmd[3:3] = ["--extractor-args", extractor_args]
    if cookie_file:
        download_cmd[3:3] = ["--cookies", str(cookie_file)]
    if cookie_browser:
        download_cmd[3:3] = ["--cookies-from-browser", cookie_browser]
    return download_cmd


FFMPEG_DIR = resolve_ffmpeg_dir()
COOKIE_BROWSERS = get_configured_cookie_browsers()
COOKIE_FILE_PATH = resolve_cookie_file()

df = pd.read_csv(INPUT_CSV)

if "channel_name" not in df.columns and "channel_title" in df.columns:
    df["channel_name"] = df["channel_title"]

total = len(df)
print(f"Total videos : {total}")
print(f"Workers      : {MAX_WORKERS}")
print(f"Delay        : {REQUEST_DELAY_SECONDS:.1f}s")
print(f"Fragments    : {FRAGMENT_CONCURRENCY}")
if YOUTUBE_EXTRACTOR_ARGS:
    print(f"Extractor    : {YOUTUBE_EXTRACTOR_ARGS}")

already_done = set()
for community_folder in os.listdir(AUDIO_DIR):
    folder_path = os.path.join(AUDIO_DIR, community_folder)
    if os.path.isdir(folder_path):
        for fname in os.listdir(folder_path):
            if fname.endswith(".mp3"):
                vid = fname.replace(".mp3", "").split("__")[-1]
                already_done.add(vid)

print(f"Already done : {len(already_done)}")
print(f"Remaining    : {total - len(already_done)}")
if COOKIE_FILE_PATH:
    print(f"Cookies      : file {COOKIE_FILE_PATH}")
elif COOKIE_BROWSERS:
    print(f"Cookies      : enabled for {', '.join(COOKIE_BROWSERS)}")
else:
    print("Cookies      : disabled (set YTDLP_COOKIE_FILE or YTDLP_COOKIE_MODE)")
print("")

success_count = 0
failed_count = 0
skipped_count = 0
auth_required_count = 0
auth_required_rows = []


def download_video(row):
    video_id = str(row["video_id"]).strip()
    community = str(row["community"]).strip().replace(" ", "_")
    channel_name = str(row["channel_name"]).strip().replace(" ", "_")
    duration = row.get("duration_seconds", 0)

    if video_id in already_done:
        return video_id, "skipped", ""

    try:
        dur = float(duration)
        if dur < MIN_DURATION:
            return video_id, "skipped_short", f"duration {dur:.0f}s < 600s"
    except (TypeError, ValueError):
        pass

    community_dir = os.path.join(AUDIO_DIR, community)
    os.makedirs(community_dir, exist_ok=True)

    output_path = os.path.join(community_dir, f"{channel_name}__{video_id}.mp3")
    url = f"https://www.youtube.com/watch?v={video_id}"
    if REQUEST_DELAY_SECONDS > 0:
        time.sleep(REQUEST_DELAY_SECONDS)

    try:
        download_succeeded = False
        last_error = None
        attempts = []
        extractor_profiles = [None]
        if YOUTUBE_EXTRACTOR_ARGS:
            extractor_profiles.append(YOUTUBE_EXTRACTOR_ARGS)

        if COOKIE_FILE_PATH:
            for extractor_args in extractor_profiles:
                attempts.append(
                    {
                        "cookie_file": COOKIE_FILE_PATH,
                        "cookie_browser": None,
                        "extractor_args": extractor_args,
                    }
                )
        for browser in COOKIE_BROWSERS:
            for extractor_args in extractor_profiles:
                attempts.append(
                    {
                        "cookie_file": None,
                        "cookie_browser": browser,
                        "extractor_args": extractor_args,
                    }
                )
        for extractor_args in extractor_profiles:
            attempts.append(
                {
                    "cookie_file": None,
                    "cookie_browser": None,
                    "extractor_args": extractor_args,
                }
            )

        for attempt in attempts:
            cookie_browser = attempt["cookie_browser"]
            cookie_file = attempt["cookie_file"]
            extractor_args = attempt["extractor_args"]
            try:
                subprocess.run(
                    build_download_cmd(
                        url,
                        output_path,
                        FFMPEG_DIR,
                        cookie_browser=cookie_browser,
                        cookie_file=cookie_file,
                        extractor_args=extractor_args,
                    ),
                    check=True,
                    timeout=DOWNLOAD_TIMEOUT,
                    capture_output=True,
                    text=True,
                )
                download_succeeded = True
                break
            except subprocess.CalledProcessError as e:
                stderr = e.stderr or ""
                last_error = e
                dpapi_failed = "Failed to decrypt with DPAPI" in stderr
                cookie_db_locked = (
                    "Could not copy" in stderr and "cookie database" in stderr
                )
                cookie_browser_unavailable = (
                    "could not find browser" in stderr.lower()
                    or "unsupported browser" in stderr.lower()
                )
                auth_blocked = (
                    "from-browser or --cookies" in stderr
                    or "Sign in to confirm" in stderr
                )
                auth_help = (
                    "Authentication required. Export YouTube cookies to "
                    "youtube_cookies.txt in the project root or set "
                    "YTDLP_COOKIE_FILE to a Netscape cookies file."
                )

                if dpapi_failed and cookie_browser is not None:
                    continue
                if cookie_db_locked and cookie_browser is not None:
                    continue
                if cookie_browser_unavailable and cookie_browser is not None:
                    continue
                if auth_blocked and (cookie_browser is not None or cookie_file is not None):
                    time.sleep(AUTH_RETRY_WAIT)
                    continue
                if auth_blocked and extractor_args is None and YOUTUBE_EXTRACTOR_ARGS:
                    continue
                if auth_blocked:
                    return video_id, "auth_required", auth_help
                raise

        if not download_succeeded:
            if last_error is not None:
                raise last_error
            raise RuntimeError(f"Download failed without a captured error for {video_id}")

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Expected output file was not created: {output_path}")

        return video_id, "success", ""

    except subprocess.CalledProcessError as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        err = e.stderr[-300:] if e.stderr else "no error message"
        return video_id, "failed", err

    except (FileNotFoundError, RuntimeError) as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return video_id, "failed", str(e)

    except subprocess.TimeoutExpired:
        if os.path.exists(output_path):
            os.remove(output_path)
        return video_id, "timeout", ""


rows = [row for _, row in df.iterrows()]

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(download_video, row): row for row in rows}

    done = 0
    for future in as_completed(futures):
        video_id, status, reason = future.result()
        done += 1

        if status == "success":
            success_count += 1
            print(f"[{done}/{total}] OK      : {video_id}")
        elif status == "skipped":
            skipped_count += 1
            print(f"[{done}/{total}] SKIP    : {video_id} (already downloaded)")
        elif status == "skipped_short":
            skipped_count += 1
            print(f"[{done}/{total}] SKIP    : {video_id} ({reason})")
        elif status == "failed":
            failed_count += 1
            print(f"[{done}/{total}] FAILED  : {video_id}")
            if reason:
                print(f"    REASON : {reason}")
        elif status == "auth_required":
            auth_required_count += 1
            failed_count += 1
            row = futures[future]
            auth_required_rows.append(
                {
                    "video_id": video_id,
                    "community": row.get("community", ""),
                    "channel_name": row.get("channel_name", row.get("channel_title", "")),
                    "reason": reason,
                }
            )
            print(f"[{done}/{total}] AUTH    : {video_id}")
            if reason:
                print(f"    REASON : {reason}")
        elif status == "timeout":
            failed_count += 1
            print(f"[{done}/{total}] TIMEOUT : {video_id}")

        if done % 50 == 0:
            print(
                f"\n--- Progress: OK {success_count}  FAILED {failed_count}  "
                f"SKIPPED {skipped_count} ---\n"
            )

print(f"\n{'=' * 50}")
print("DOWNLOAD COMPLETE")
print(f"{'=' * 50}")

if auth_required_rows:
    pd.DataFrame(auth_required_rows).drop_duplicates(subset=["video_id"]).to_csv(
        AUTH_REQUIRED_CSV, index=False
    )

print(f"Downloaded : {success_count}")
print(f"Skipped    : {skipped_count}")
print(f"Failed     : {failed_count}")
print(f"Auth need  : {auth_required_count}")
print(f"Audio in   : {AUDIO_DIR}")
if auth_required_rows:
    print(f"Retry list : {AUTH_REQUIRED_CSV}")
    print("Next step  : export YouTube cookies to youtube_cookies.txt and rerun.")

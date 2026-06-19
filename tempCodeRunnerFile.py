
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
import httpx
import pathlib

from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from tusclient import client

from config import settings
from utils  import extract_uid_from_url

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"

headers = {
    "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"
}

async def get_token_url(video_id: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/stream/{video_id}/token",
            headers=headers
        )
        response.raise_for_status()
        token = response.json()["result"]["token"]
        return f"https://videodelivery.net/{video_id}/manifest/video.m3u8?token={token}"

def list_existing_videos() -> set[str]:
    existing = set()
    seen_ids = set()
    page = 1

    while True:
        res = httpx.get(
            f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream",
            headers=headers,
            params={"page": page, "per_page": 100}
        )
        res.raise_for_status()
        videos = res.json()["result"]

        new_ids = {v["uid"] for v in videos}
        if not new_ids or new_ids.issubset(seen_ids):
            break

        seen_ids.update(new_ids)
        existing.update(new_ids)
        page += 1

    return existing

def upload_video(file_path: str, name: str) -> str:
    file = pathlib.Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    tus = client.TusClient(
        f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream",
        headers={
            "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"
        }
    )

    uploader = tus.uploader(str(file), chunk_size=5 * 1024 * 1024)  # 5MB

    uploader.metadata = {
        "name": name
    }

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Uploading...", total=uploader.get_file_size())

        while uploader.offset < uploader.get_file_size():
            uploader.upload_chunk()
            progress.update(task, completed=uploader.offset)

    video_id = uploader.request.response_headers.get('stream-media-id')

    return video_id
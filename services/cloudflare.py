import httpx
import pathlib

from typing import Optional

from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from tusclient import client

from config import settings

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}"

headers = {
    "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"
}

async def delete_video_by_id(video_id: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BASE_URL}/stream/{video_id}",
            headers=headers
        )
        if response.status_code == 200:
            return True
        return False

async def generate_signed_url(video_id: str) -> str:
    resp = await httpx.AsyncClient().post(
        f"{BASE_URL}/stream/{video_id}/token",
        headers=headers
    )
    resp.raise_for_status()
    token = resp.json()["result"]["token"]
    return f"https://{settings.CLOUDFLARE_CUSTOMER_SUBDOMAIN}/{token}/iframe"

async def list_videos(
    search: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> list[dict]:
    params: dict = {}
    if search:
        params["search"] = search
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/stream",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json().get("result", [])


def upload_video(file_path: str, name: str, metadata: dict[str, str]) -> str:
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
        "name": name,
        "requiresignedurls": "true",
        **metadata
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
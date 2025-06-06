import asyncio
import httpx
import questionary
import typer
from rich.console import Console
from typing import Optional

from config import settings
from models.video import Video, Category
from services.cloudflare import get_token_url, list_existing_videos, upload_video
from services.video_store import VideoStore

app = typer.Typer(help="Manage Cloudflare Stream videos")
console = Console()
store = VideoStore()

@app.command("sync")
def sync_videos():
    """Sync local video store with Cloudflare — remove stale entries."""
    console.print("[bold blue]Syncing local video metadata with Cloudflare...[/bold blue]")

    existing = list_existing_videos()

    removed = store.delete_by_ids(existing)
    console.print(f"[green]Sync complete.[/green] Removed {removed} stale video(s).")

@app.command("list")
def list_videos(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    pages: int = typer.Option(5, help="How many videos to list"),
    query: Optional[str] = typer.Option(None, help="Search in title or description")
):
    """List videos with optional filtering and interactive selection."""
    videos = store.list_videos()

    if category:
        videos = [v for v in videos if v.category == category]

    if query:
        videos = [
            v for v in videos
            if query.lower() in v.title.lower() or query.lower() in (v.description or "").lower()
        ]

    videos = videos[:pages]

    if not videos:
        console.print("[yellow]No videos found.[/yellow]")
        raise typer.Exit()

    choices = [
        f"{i+1}. Title: '{v.title}', Description: '{v.description}'"
        for i, v in enumerate(videos)
    ]

    selected = questionary.select(
        "Select a video to get its playback URL",
        choices=choices
    ).ask()

    index = choices.index(selected)
    video = videos[index]

    async def fetch_token():
        return await get_token_url(video.video_id)

    signed_url = asyncio.run(fetch_token())

    console.print("\n[bold green]Selected Video[/bold green]")
    console.print(f"Title: {video.title}")
    console.print(f"Description: {video.description}")
    console.print(f"Category: {video.category}")
    console.print(f"URL: {signed_url}")

@app.command()
def upload(path: str):
    """Upload a video file to Cloudflare Stream."""
    title = typer.prompt("Title", default="Test video")
    description = typer.prompt("Description", default="This is a test video")

    category = questionary.select(
        "Select category:",
        choices=list(Category.__args__)
    ).ask()

    async def process():
        uid = upload_video(path, title)

        video = Video(
            category=category,
            video_id=uid,
            description=description,
            title=title
        )

        store.save_video(video)
        console.print(f"[green]Upload complete. Video ID: {uid}[/green]")

    asyncio.run(process())

if __name__ == "__main__":
    app()

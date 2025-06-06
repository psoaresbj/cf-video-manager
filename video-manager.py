import asyncio
import questionary
import typer
import httpx

from rich.console import Console
from typing import Optional

from constants.category import Category
from services.cloudflare import delete_video_by_id, generate_signed_url, list_videos, upload_video

app = typer.Typer(help="Manage Cloudflare Stream videos")
console = Console()

@app.command(name="list", help="List and manage videos")
def list_videos_command(
    search: Optional[str] = typer.Option(None, help="Search by title or meta.name"),
    start: Optional[str] = typer.Option(None, help="ISO date to list videos created after"),
    end: Optional[str] = typer.Option(None, help="ISO date to list videos created before"),
    category: Optional[str] = typer.Option(None, help="Filter by category in metadata"),
):
    try:
        get_videos = list_videos(search=search, start=start, end=end)

        videos = asyncio.run(get_videos)
    except httpx.HTTPError as e:
        console.print(f"[red]Error fetching videos: {e}[/red]")
        raise typer.Exit(code=1)

    if category:
        videos = [v for v in videos if v.get("meta", {}).get("category") == category]

    if not videos:
        console.print("[yellow]No videos found with the given criteria.[/yellow]")
        raise typer.Exit()

    choices = [
        f"{i+1}. ID: '{v['uid']}', Title: '{v.get('meta', {}).get('title', '')}'"
        for i, v in enumerate(videos)
    ]

    while True:
        selected = questionary.select("Select a video", choices=choices + ["Exit"]).ask()
        if selected == "Exit":
            break

        index = choices.index(selected)
        video = videos[index]
        video_id = video["uid"]
        title = video.get("meta", {}).get("title", "Untitled")

        action = questionary.select(
            f"What do with '{title}'?",
            choices=["Preview", "Delete", "Back"]
        ).ask()

        if action == "Preview":
            url = asyncio.run(generate_signed_url(video_id))
            console.print("\n[bold green]Signed Iframe URL[/bold green]")
            console.print(url)

        elif action == "Delete":
            confirm = questionary.confirm(f"Delete '{title}'?").ask()
            if confirm:
                success = asyncio.run(delete_video_by_id(video_id))
                console.print("[red]Deleted![/red]" if success else "[red]Delete failed.[/red]")
                if success:
                    videos.pop(index)
                    choices.pop(index)
                    if not videos:
                        console.print("[yellow]No more videos.[/yellow]")
                        break

        elif action == "Back":
            continue


@app.command(name="upload", help="Upload a new video")
def upload(path: str):
    title = typer.prompt("Title")
    description = typer.prompt("Description")

    category = questionary.select(
        "Select category:",
        choices=list(Category.__args__)
    ).ask()

    async def process():
        video_id = upload_video(
            path,
            name=title,
            metadata={
                "title": title,
                "description": description,
                "category": category
            }
        )

        console.print(f"[green]Upload complete. Video ID: {video_id}[/green]")

    asyncio.run(process())

if __name__ == "__main__":
    app()

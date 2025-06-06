# Cloudflare Stream Video Manager

A CLI tool for uploading and managing private videos on Cloudflare Stream. It supports metadata entry, secure token-based playback, and stores all metadata locally in a version-controlled JSON file.

## Features

- Upload videos to Cloudflare Stream from the terminal
- Prompt for and store metadata (`title`, `description`, `category`)
- List videos with filtering by category and search term
- Retrieve private, tokenized playback URLs
- Store metadata in `data/videos.json`
- Fully interactive CLI using `Typer`, `Rich`, and `Questionary`

## Requirements

- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) (install via `pipx install uv`)
- Cloudflare Stream account with read/write API tokens

## Setup

1. **Clone the repo**
2. **Create a `.env` file** with:
   ```env
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_write_token
   ```
3. **Install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   uv pip install -r pyproject.toml
   ```

## CLI Usage

```bash
python video-manager.py --help
```

### Upload a video
```bash
python video-manager.py upload path/to/video.mp4
```
- Prompts for title, description, category
- Uploads to Cloudflare Stream
- Saves metadata locally

### List and fetch a playback URL
```bash
python video-manager.py list --category misc --query "misc" --pages 10
```
- Interactive list of stored videos
- Select to get a secure playback URL

## Storage

All metadata is stored in `data/videos.json` and is safe to commit to version control.

## Security

Videos are kept private on Cloudflare. The CLI retrieves tokenized playback URLs via Cloudflare’s `/token` endpoint — only apps with access to this CLI (or API token) can generate valid playback URLs.

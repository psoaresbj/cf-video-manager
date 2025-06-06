import json

from pathlib import Path
from typing import List, Optional

from models.video import Video

class VideoStore:
    def __init__(self, path: str = "data/videos.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def delete_by_ids(self, ids: set[str]) -> int:
        videos = self._read()
        kept = [v for v in videos if v.video_id in ids]

        removed = len(videos) - len(kept)
        if removed > 0:
            self._write(kept)
        return removed

    def delete_video(self, video_id: str) -> bool:
        videos = self._read()
        new_videos = [v for v in videos if v.video_id != video_id]
        if len(new_videos) == len(videos):
            return False  # nothing deleted
        self._write(new_videos)
        return True

    def _read(self) -> List[Video]:
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [Video(**item) for item in data]

    def _write(self, videos: List[Video]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump([video.model_dump() for video in videos], f, indent=2)

    def list_videos(self) -> List[Video]:
        return self._read()

    def get_video(self, video_id: str) -> Optional[Video]:
        return next((v for v in self._read() if v.video_id == video_id), None)

    def save_video(self, video: Video) -> None:
        videos = self._read()
        videos = [v for v in videos if v.video_id != video.video_id]
        videos.append(video)
        self._write(videos)

    def update_metadata(self, video_id: str, update: dict) -> Optional[Video]:
        videos = self._read()
        for i, v in enumerate(videos):
            if v.video_id == video_id:
                updated = v.model_copy(update=update)
                videos[i] = updated
                self._write(videos)
                return updated
        return None

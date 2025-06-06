from pydantic import BaseModel, Field

from constants.category import Category

class Video(BaseModel):
    category: Category = Field(default="misc", description="Category of the video")
    video_id: str = Field(..., description="Cloudflare video Unique identifier")
    description: str = Field(..., description="Description of the video")
    title: str = Field(..., description="Title of the video")

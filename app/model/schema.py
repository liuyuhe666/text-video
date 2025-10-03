from pydantic import BaseModel
from enum import Enum
from typing import Optional, Any, Union


class BaseResponse(BaseModel):
    status: int = 200
    message: Optional[str] = "success"
    data: Any = None


class TaskResponse(BaseResponse):
    class TaskResponseData(BaseModel):
        task_id: str

    data: TaskResponseData

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {"task_id": "6c85c8cc-a77a-42b9-bc30-947815aa0558"},
            },
        }


class VideoAspect(str, Enum):
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape.value:
            return 1920, 1080
        elif self == VideoAspect.portrait.value:
            return 1080, 1920
        elif self == VideoAspect.square.value:
            return 1080, 1080
        return 1080, 1920


class VideoRequest(BaseModel):
    video_aspect: Optional[VideoAspect] = VideoAspect.portrait.value

    text_content: str = ""

    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural"
    voice_volume: Optional[str] = "+0%"
    voice_rate: Optional[str] = "+0%"

    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Union[bool, str] = True

    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5


class AudioRequest(BaseModel):
    text_content: str = ""

    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural"
    voice_volume: Optional[str] = "+0%"
    voice_rate: Optional[str] = "+0%"

    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Union[bool, str] = True

    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5

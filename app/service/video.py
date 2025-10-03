import os
import pysrt
from loguru import logger
from app.model.schema import VideoRequest, VideoAspect
from app.util import util
from moviepy import *
from moviepy.tools import convert_to_seconds


audio_codec = "aac"
video_codec = "libx264"
fps = 30


def generate_video(
        audio_path: str,
        subtitle_path: str,
        output_path: str,
        params: VideoRequest
):
    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"generating video: {video_width} x {video_height}")
    logger.info(f"  ② audio: {audio_path}")
    logger.info(f"  ③ subtitle: {subtitle_path}")
    logger.info(f"  ④ output: {output_path}")

    output_dir = os.path.dirname(output_path)
    font_path = ""
    if not params.font_name:
        params.font_name = "STHeitiMedium.ttc"
    font_path = os.path.join(util.font_dir(), params.font_name)
    if os.name == "nt":
        font_path = font_path.replace("\\", "/")
    logger.info(f"  ⑤ font: {font_path}")

    subtitle_list = pysrt.open(subtitle_path)
    text_clip_list = []
    for subtitle in subtitle_list:
        text_clip = TextClip(
            text=subtitle.text,
            font=font_path,
            font_size=params.font_size,
            size=(video_width, video_height),
            text_align="center",
            margin=(10, 0),
            method="caption",
            color=params.text_fore_color,
            bg_color=params.text_background_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            duration=convert_to_seconds(str(subtitle.duration)))
        text_clip_list.append(text_clip)
    final_clip = concatenate_videoclips(text_clip_list)
    audio_clip = AudioFileClip(audio_path)
    final_clip = final_clip.with_audio(audio_clip)
    final_clip.write_videofile(output_path,
                               audio_codec=audio_codec,
                               codec=video_codec,
                               temp_audiofile_path=output_dir,
                               logger=None,
                               fps=fps)
    final_clip.close()
    del final_clip

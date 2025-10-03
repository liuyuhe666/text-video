import os
from app.model.schema import VideoRequest
from loguru import logger
from app.service import state as sm
from app.model import constant
from app.util import util
from app.service.audio import generate_audio
from app.service.video import generate_video


def _generate_audio(task_id, params):
    audio_path = os.path.join(util.task_dir(task_id), "audio.mp3")
    subtitle_path = os.path.join(util.task_dir(task_id), "subtitle.srt")
    try:
        generate_audio(audio_path, subtitle_path, params)
    except Exception as e:
        logger.error(f"生成音频失败: {e}")
        return None, None
    return audio_path, subtitle_path


def _generate_video(task_id, params, audio_path, subtitle_path):
    video_path = os.path.join(util.task_dir(task_id), "video.mp4")
    try:
        generate_video(audio_path, subtitle_path,
                       output_path=video_path, params=params)
    except Exception as e:
        logger.error(f"生成视频失败: {e}")
        return None
    return video_path


def start(task_id, params: VideoRequest, stop_at: str = "video"):
    logger.info(f"start task: {task_id}, stop_at: {stop_at}")
    sm.state.update_task(
        task_id, state=constant.TASK_STATE_PROCESSING, progress=5)
    # 生成音频
    audio_path, subtitle_path = _generate_audio(task_id, params)
    if not audio_path:
        sm.state.update_task(task_id, state=constant.TASK_STATE_FAILED)
        return
    sm.state.update_task(
        task_id, state=constant.TASK_STATE_PROCESSING, progress=50)
    if stop_at == "audio":
        sm.state.update_task(
            task_id,
            state=constant.TASK_STATE_COMPLETE,
            progress=100,
            audio_file=audio_path,
        )
        return {"audio": audio_path}
    # 生成视频
    video_path = _generate_video(task_id, params, audio_path, subtitle_path)
    if not video_path:
        sm.state.update_task(task_id, state=constant.TASK_STATE_FAILED)
        return
    logger.success(
        f"task {task_id} finished."
    )
    kwargs = {
        "video": video_path,
        "audio": audio_path,
        "subtitle": subtitle_path,
    }
    sm.state.update_task(
        task_id, state=constant.TASK_STATE_COMPLETE, progress=100, **kwargs
    )
    return kwargs


if __name__ == "__main__":
    task_id = "test-1"
    params = VideoRequest(
        text_content="中国早在8月即宣布10月1日起推行“K字签证”，这一面向海外人士的新签证类型在中国社交媒体上引起轩然大波。",
        voice_name="zh-CN-XiaoxiaoNeural",
        voice_rate="-4%",
        voice_volume="+1%"
    )
    result = start(task_id, params, stop_at="video")
    print(result)

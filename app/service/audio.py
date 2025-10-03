import edge_tts
from app.model.schema import VideoRequest


def generate_audio(
        audio_path: str,
        subtitle_path: str,
        params: VideoRequest
):
    communicate = edge_tts.Communicate(text=params.text_content,
                                       voice=params.voice_name,
                                       rate=params.voice_rate,
                                       volume=params.voice_volume)
    submaker = edge_tts.SubMaker()
    with open(audio_path, "wb") as file:
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    with open(subtitle_path, "w", encoding="utf-8") as file:
        file.write(submaker.get_srt())

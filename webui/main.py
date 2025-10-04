from loguru import logger
from uuid import uuid4
import platform
import streamlit as st
import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    print("******** sys.path ********")
    print(sys.path)
    print("")
font_dir = os.path.join(root_dir, "resource", "fonts")

from app.model.schema import VideoRequest, VideoAspect  # NOQA: E402
from app.util import util  # NOQA: E402
from app.service import task as tm  # NOQA: E402


def init_log():
    logger.remove()
    _lvl = "DEBUG"

    def format_record(record):
        # 获取日志记录中的文件全路径
        file_path = record["file"].path
        # 将绝对路径转换为相对于项目根目录的路径
        relative_path = os.path.relpath(file_path, root_dir)
        # 更新记录中的文件路径
        record["file"].path = f"./{relative_path}"
        # 返回修改后的格式字符串
        # 您可以根据需要调整这里的格式
        record["message"] = record["message"].replace(root_dir, ".")

        _format = (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>"
            + "\n"
        )
        return _format

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
    )


init_log()


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def open_task_folder(task_id):
    try:
        sys = platform.system()
        path = os.path.join(root_dir, "storage", "tasks", task_id)
        if os.path.exists(path):
            if sys == "Windows":
                os.system(f"start {path}")
            if sys == "Darwin":
                os.system(f"open {path}")
    except Exception as e:
        logger.error(e)


st.set_page_config(
    page_title="Text Video",
    page_icon="✨",
    layout="wide"
)
st.write("""
# ✨ 文字视频
""")
params = VideoRequest()
if "text_content" not in st.session_state:
    st.session_state["text_content"] = ""
with st.container(border=True):
    st.write("**视频设置**")
    params.text_content = st.text_area("视频内容",
                                       value=st.session_state["text_content"],
                                       height=280)
    video_aspect_ratios = [
        ("竖屏 9:16", VideoAspect.portrait.value),
        ("横屏 16:9", VideoAspect.landscape.value),
    ]
    selected_index = st.selectbox(
        "视频比例",
        options=range(len(video_aspect_ratios)),
        format_func=lambda x: video_aspect_ratios[x][0]
    )
    params.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])
    params.voice_name = st.selectbox(
        "朗读声音",
        options=["zh-CN-XiaoxiaoNeural", "zh-CN-YunjianNeural"],
        index=0
    )
    params.voice_volume = st.selectbox(
        "朗读音量",
        options=["-50%", "-40%", "-30%", "-20%", "-10%",
                 "+0%", "+10%", "+20%", "+30%", "+40%", "+50%"],
        index=5,
    )

    params.voice_rate = st.selectbox(
        "朗读速度",
        options=["-50%", "-40%", "-30%", "-20%", "-10%",
                         "+0%", "+10%", "+20%", "+30%", "+40%", "+50%"],
        index=5,
    )
    font_name_list = get_all_fonts()
    params.font_name = st.selectbox(
        "字体",
        options=font_name_list,
        index=0
    )
    font_cols = st.columns([0.3, 0.7])
    with font_cols[0]:
        params.text_fore_color = st.color_picker(
            "文字颜色", "#FFFFFF"
        )
    with font_cols[1]:
        params.font_size = st.slider("文字大小", 30, 100, 60)

    stroke_cols = st.columns([0.3, 0.7])
    with stroke_cols[0]:
        params.stroke_color = st.color_picker("描边颜色", "#000000")
    with stroke_cols[1]:
        params.stroke_width = st.slider("描边粗细", 0.0, 10.0, 1.5)

start_button = st.button("生成视频", use_container_width=True, type="primary")
if start_button:
    task_id = str(uuid4())
    if not params.text_content:
        st.error("视频内容不能为空！！！")
        st.stop()

    log_container = st.empty()
    log_records = []

    def log_received(msg):
        with log_container:
            log_records.append(msg)
            st.code("\n".join(log_records))

    logger.add(log_received)
    st.toast("正在生成视频")
    logger.info("开始生成视频")
    logger.info(util.to_json(params))
    result = tm.start(task_id=task_id, params=params)
    if not result or "video" not in result:
        st.error("视频生成失败")
        logger.error("视频生成失败")
        st.stop()
    video = result.get("video", "")
    st.video(data=video)
    st.success("视频生成成功")
    open_task_folder(task_id)
    logger.info("视频生成完成")

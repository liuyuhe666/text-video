import os
import pathlib
import shutil
from fastapi import APIRouter, Request, BackgroundTasks, Depends, Path
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import Query
from uuid import uuid4
from typing import Union
from loguru import logger
from app.config import config
from app.util import util
from app.model.exception import HttpException
from app.manager.memory_manager import InMemoryTaskManager
from app.model.schema import (
    TaskResponse,
    VideoRequest,
    AudioRequest,
    TaskQueryResponse,
    TaskDeletionResponse,
    TaskQueryRequest
)
from app.service import state as sm
from app.service import task as tm


router = APIRouter()
router.prefix = "/api"

_max_concurrent_tasks = config.app.get("max_concurrent_tasks", 5)
task_manager = InMemoryTaskManager(max_concurrent_tasks=_max_concurrent_tasks)


def get_task_id(request: Request):
    task_id = request.headers.get("x-task-id")
    if not task_id:
        task_id = uuid4()
    return str(task_id)


@router.post("/video", response_model=TaskResponse, summary="生成视频")
def create_video(
    background_tasks: BackgroundTasks,
    request: Request,
    body: VideoRequest
):
    return create_task(request, body, stop_at="video")


@router.post("/audio", response_model=TaskResponse, summary="生成音频")
def create_audio(
    background_tasks: BackgroundTasks,
    request: Request,
    body: AudioRequest
):
    return create_task(request, body, stop_at="audio")


def create_task(
    request: Request,
    body: Union[VideoRequest, AudioRequest],
    stop_at: str,
):
    task_id = util.get_uuid()
    request_id = get_task_id(request)
    try:
        task = {
            "task_id": task_id,
            "request_id": request_id,
            "params": body.model_dump(),
        }
        sm.state.update_task(task_id)
        task_manager.add_task(tm.start, task_id=task_id,
                              params=body, stop_at=stop_at)
        logger.success(f"Task created: {util.to_json(task)}")
        return util.get_response(200, task)
    except ValueError as e:
        raise HttpException(
            task_id=task_id, status_code=400, message=f"{request_id}: {str(e)}"
        )


@router.get("/stream/{file_path:path}")
async def stream_video(request: Request, file_path: str):
    tasks_dir = util.task_dir()
    video_path = os.path.join(tasks_dir, file_path)
    range_header = request.headers.get("Range")
    video_size = os.path.getsize(video_path)
    start, end = 0, video_size - 1

    length = video_size
    if range_header:
        range_ = range_header.split("bytes=")[1]
        start, end = [
            int(part) if part else None for part in range_.split("-")]
        if start is None:
            start = video_size - end
            end = video_size - 1
        if end is None:
            end = video_size - 1
        length = end - start + 1

    def file_iterator(file_path, offset=0, bytes_to_read=None):
        with open(file_path, "rb") as f:
            f.seek(offset, os.SEEK_SET)
            remaining = bytes_to_read or video_size
            while remaining > 0:
                bytes_to_read = min(4096, remaining)
                data = f.read(bytes_to_read)
                if not data:
                    break
                remaining -= len(data)
                yield data

    response = StreamingResponse(
        file_iterator(video_path, start, length), media_type="video/mp4"
    )
    response.headers["Content-Range"] = f"bytes {start}-{end}/{video_size}"
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Content-Length"] = str(length)
    response.status_code = 206  # Partial Content

    return response


@router.get("/download/{file_path:path}")
async def download_video(_: Request, file_path: str):
    tasks_dir = util.task_dir()
    video_path = os.path.join(tasks_dir, file_path)
    file_path = pathlib.Path(video_path)
    filename = file_path.stem
    extension = file_path.suffix
    headers = {
        "Content-Disposition": f"attachment; filename={filename}{extension}"}
    return FileResponse(
        path=video_path,
        headers=headers,
        filename=f"{filename}{extension}",
        media_type=f"video/{extension[1:]}",
    )


@router.get("/tasks", response_model=TaskQueryResponse, summary="获取全部任务")
def get_all_tasks(request: Request, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    tasks, total = sm.state.get_all_tasks(page, page_size)
    response = {
        "tasks": tasks,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    return util.get_response(200, response)


@router.get(
    "/tasks/{task_id}", response_model=TaskQueryResponse, summary="根据任务ID获取任务"
)
def get_task(
    request: Request,
    task_id: str = Path(..., description="Task ID"),
    query: TaskQueryRequest = Depends(),
):
    endpoint = config.app.get("endpoint", "")
    if not endpoint:
        endpoint = str(request.base_url)
    endpoint = endpoint.rstrip("/")

    request_id = get_task_id(request)
    task = sm.state.get_task(task_id)
    if task:
        task_dir = util.task_dir()

        def file_to_uri(file):
            if not file.startswith(endpoint):
                _uri_path = file.replace(task_dir, "tasks").replace("\\", "/")
                _uri_path = f"{endpoint}/{_uri_path}"
            else:
                _uri_path = file
            return _uri_path

        if "file" in task:
            task["file"] = file_to_uri(task["file"])
        return util.get_response(200, task)

    raise HttpException(
        task_id=task_id, status_code=404, message=f"{request_id}: task not found"
    )


@router.delete(
    "/tasks/{task_id}",
    response_model=TaskDeletionResponse,
    summary="根据任务ID删除任务",
)
def delete_video(request: Request, task_id: str = Path(..., description="Task ID")):
    request_id = get_task_id(request)
    task = sm.state.get_task(task_id)
    if task:
        tasks_dir = util.task_dir()
        current_task_dir = os.path.join(tasks_dir, task_id)
        if os.path.exists(current_task_dir):
            shutil.rmtree(current_task_dir)

        sm.state.delete_task(task_id)
        logger.success(f"video deleted: {util.to_json(task)}")
        return util.get_response(200)

    raise HttpException(
        task_id=task_id, status_code=404, message=f"{request_id}: task not found"
    )

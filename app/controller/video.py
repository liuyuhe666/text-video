from fastapi import APIRouter, Request, BackgroundTasks
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
    AudioRequest
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


@router.post("/video", response_model=TaskResponse, summary="Generate video")
def create_video(
    background_tasks: BackgroundTasks,
    request: Request,
    body: VideoRequest
):
    return create_task(request, body, stop_at="video")


@router.post("/audio", response_model=TaskResponse, summary="Generate audio only")
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

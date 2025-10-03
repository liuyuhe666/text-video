from abc import ABC, abstractmethod
from app.model import constant


# Base class for state management
class BaseState(ABC):
    @abstractmethod
    def update_task(self, task_id: str, state: int, progress: int = 0, **kwargs):
        pass

    @abstractmethod
    def get_task(self, task_id: str):
        pass

    @abstractmethod
    def get_all_tasks(self, page: int, page_size: int):
        pass


# Memory state management
class MemoryState(BaseState):
    def __init__(self):
        self._tasks = {}

    def get_all_tasks(self, page: int, page_size: int):
        start = (page - 1) * page_size
        end = start + page_size
        tasks = list(self._tasks.values())
        total = len(tasks)
        return tasks[start:end], total

    def update_task(
        self,
        task_id: str,
        state: int = constant.TASK_STATE_PROCESSING,
        progress: int = 0,
        **kwargs,
    ):
        progress = int(progress)
        if progress > 100:
            progress = 100

        self._tasks[task_id] = {
            "task_id": task_id,
            "state": state,
            "progress": progress,
            **kwargs,
        }

    def get_task(self, task_id: str):
        return self._tasks.get(task_id, None)

    def delete_task(self, task_id: str):
        if task_id in self._tasks:
            del self._tasks[task_id]


state = MemoryState()

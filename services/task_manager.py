# services/task_manager.py

from typing import Any, Dict, Optional, Callable, Coroutine, TypeVar
import asyncio
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid

T = TypeVar("T")


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskManager:
    def __init__(
        self,
        max_concurrent_tasks: int = 10,  # TODO: Move to config
        max_queue_size: int = 1000,  # TODO: Move to config
        num_workers: int = 3,  # TODO: Move to config
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_queue_size = max_queue_size
        self.num_workers = num_workers

        # Queues for different priority levels
        self.queues: Dict[TaskPriority, asyncio.PriorityQueue] = {
            priority: asyncio.PriorityQueue(maxsize=max_queue_size)
            for priority in TaskPriority
        }

        # Track active tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, TaskResult] = {}

        # Semaphore to limit concurrent tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Worker tasks
        self.workers: list[asyncio.Task] = []
        self.running = False

        # Locks for specific chat_ids
        self.chat_locks: Dict[int, asyncio.Lock] = {}

        self.logger = logging.getLogger("TaskManager")

    async def start(self):
        """Start the task manager workers"""
        if self.running:
            return

        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i)) for i in range(self.num_workers)
        ]
        self.logger.info(f"Started {self.num_workers} task manager workers")

    async def stop(self):
        """Stop the task manager and clean up"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Cancel any remaining active tasks
        for task_id, task in self.active_tasks.items():
            task.cancel()
            self.results[task_id].status = TaskStatus.CANCELLED

        self.workers.clear()
        self.active_tasks.clear()
        self.logger.info("Task manager stopped")

    async def add_task(
        self,
        callback: Callable[..., Coroutine[Any, Any, T]],
        chat_id: int,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs,
    ) -> str:
        """Add a new task to the queue"""
        if not self.running:
            raise RuntimeError("Task manager is not running")

        task_id = str(uuid.uuid4())

        # Create result placeholder
        self.results[task_id] = TaskResult(task_id=task_id, status=TaskStatus.PENDING)

        # Create task data
        task_data = {
            "id": task_id,
            "callback": callback,
            "chat_id": chat_id,
            "kwargs": kwargs,
            "priority": priority,
            "created_at": datetime.now(),
        }

        # Add to appropriate priority queue
        await self.queues[priority].put((priority.value, task_data))

        self.logger.debug(f"Added task {task_id} to queue with priority {priority}")
        return task_id

    # TODO: Unimplemented
    async def get_result(
        self, task_id: str, timeout: Optional[float] = None
    ) -> TaskResult:
        """Get the result of a task, optionally waiting for it to complete"""
        if task_id not in self.results:
            raise KeyError(f"No task found with id {task_id}")

        result = self.results[task_id]

        if timeout and result.status == TaskStatus.PENDING:
            try:
                task = self.active_tasks.get(task_id)
                if task:
                    await asyncio.wait_for(task, timeout=timeout)
                    result = self.results[task_id]
            except asyncio.TimeoutError:
                pass

        return result

    async def _worker(self, worker_id: int):
        """Worker coroutine that processes tasks from the queues"""
        self.logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Check queues in priority order
                for priority in TaskPriority:
                    if not self.queues[priority].empty():
                        _, task_data = await self.queues[priority].get()
                        break
                else:
                    # No tasks in any queue, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                task_id = task_data["id"]
                chat_id = task_data["chat_id"]
                callback = task_data["callback"]
                kwargs = task_data["kwargs"]
                
                # Extract the original args and kwargs
                args = kwargs.pop('_args', ())
                real_kwargs = kwargs.pop('_kwargs', {})

                # Get or create chat lock
                if chat_id not in self.chat_locks:
                    self.chat_locks[chat_id] = asyncio.Lock()
                chat_lock = self.chat_locks[chat_id]

                # Execute task with semaphore and chat lock
                async with self.semaphore, chat_lock:
                    self.logger.debug(f"Starting task {task_id}")
                    self.results[task_id].status = TaskStatus.RUNNING
                    self.results[task_id].started_at = datetime.now()

                    try:
                        result = await callback(*args, **real_kwargs)
                        self.results[task_id].status = TaskStatus.COMPLETED
                        self.results[task_id].result = result
                    except Exception as e:
                        self.logger.error(f"Task {task_id} failed: {str(e)}")
                        self.results[task_id].status = TaskStatus.FAILED
                        self.results[task_id].error = e
                    finally:
                        self.results[task_id].completed_at = datetime.now()

                        # Clean up chat lock if no more tasks for this chat
                        if not any(
                            t["chat_id"] == chat_id for t in self.active_tasks.values()
                        ):
                            del self.chat_locks[chat_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on repeated errors

        self.logger.info(f"Worker {worker_id} stopped")

    # TODO: Unimplemented
    def get_queue_sizes(self) -> Dict[TaskPriority, int]:
        """Get current size of all queues"""
        return {priority: queue.qsize() for priority, queue in self.queues.items()}

    # TODO: Unimplemented
    def get_active_tasks_count(self) -> int:
        """Get number of currently running tasks"""
        return len(self.active_tasks)

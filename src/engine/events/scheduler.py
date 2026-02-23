"""事件调度器.

提供延迟、周期、条件事件的管理和执行。
"""

from __future__ import annotations

import asyncio
import heapq
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """事件类型."""

    DELAY = auto()  # 延迟执行
    INTERVAL = auto()  # 周期执行
    CONDITION = auto()  # 条件执行
    FRAME = auto()  # 每帧执行


@dataclass
class Event:
    """事件定义.

    Attributes:
        id: 唯一标识符
        event_type: 事件类型
        callback: 回调函数
        delay: 延迟/间隔时间（秒）
        condition: 条件函数
        priority: 优先级（越小越高）
        repeat: 重复次数（0表示无限）
        created_at: 创建时间
    """

    id: str
    event_type: EventType
    callback: Callable[..., Any]
    delay: float = 0.0
    condition: Callable[[], bool] | None = None
    priority: int = 0
    repeat: int = 0
    created_at: float = field(default_factory=time.time)

    def __lt__(self, other: Event) -> bool:
        """用于堆排序."""
        return self.priority < other.priority


class EventScheduler:
    """事件调度器.

    使用asyncio和优先队列管理游戏事件。

    Attributes:
        time_scale: 时间膨胀系数
        running: 是否运行中
    """

    def __init__(self, time_scale: float = 1.0) -> None:
        """初始化事件调度器.

        Args:
            time_scale: 时间膨胀系数（1.0为正常）
        """
        self._queue: list[tuple[float, int, Event]] = []  # (执行时间, 序号, 事件)
        self._time_scale = time_scale
        self._running = False
        self._task: asyncio.Task[Any] | None = None
        self._event_counter = 0  # 用于打破平局
        self._cancelled_events: set[str] = set()

        # 帧事件列表
        self._frame_events: list[Event] = []

    @property
    def time_scale(self) -> float:
        """时间膨胀系数."""
        return self._time_scale

    @time_scale.setter
    def time_scale(self, value: float) -> None:
        """设置时间膨胀系数.

        Args:
            value: 新系数（>0）
        """
        if value <= 0:
            raise ValueError("时间系数必须大于0")
        self._time_scale = value

    def set_time_scale(self, scale: float) -> None:
        """设置时间膨胀系数.

        Args:
            scale: 时间系数（1.0为正常，0.5为一半速度）
        """
        self.time_scale = scale
        logger.info(f"时间膨胀系数设置为: {scale}")

    def schedule(
        self,
        callback: Callable[..., Any],
        delay: float = 0.0,
        event_type: EventType = EventType.DELAY,
        condition: Callable[[], bool] | None = None,
        priority: int = 0,
        repeat: int = 0,
    ) -> str:
        """安排事件.

        Args:
            callback: 回调函数（必须是async def）
            delay: 延迟/间隔时间（秒）
            event_type: 事件类型
            condition: 条件函数
            priority: 优先级
            repeat: 重复次数（0表示无限）

        Returns:
            事件ID
        """
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            event_type=event_type,
            callback=callback,
            delay=delay,
            condition=condition,
            priority=priority,
            repeat=repeat,
        )

        if event_type == EventType.FRAME:
            # 帧事件直接加入帧列表
            self._frame_events.append(event)
        else:
            # 其他事件加入优先队列
            exec_time = time.time() + delay / self._time_scale
            heapq.heappush(
                self._queue,
                (exec_time, self._event_counter, event)
            )
            self._event_counter += 1

        logger.debug(f"安排事件: id={event_id}, type={event_type.name}, delay={delay}")
        return event_id

    def schedule_delay(
        self,
        callback: Callable[..., Any],
        delay: float,
        priority: int = 0,
    ) -> str:
        """安排延迟事件.

        Args:
            callback: 回调函数
            delay: 延迟时间（秒）
            priority: 优先级

        Returns:
            事件ID
        """
        return self.schedule(
            callback=callback,
            delay=delay,
            event_type=EventType.DELAY,
            priority=priority,
        )

    def schedule_interval(
        self,
        callback: Callable[..., Any],
        interval: float,
        repeat: int = 0,
        priority: int = 0,
    ) -> str:
        """安排周期事件.

        Args:
            callback: 回调函数
            interval: 间隔时间（秒）
            repeat: 重复次数（0为无限）
            priority: 优先级

        Returns:
            事件ID
        """
        return self.schedule(
            callback=callback,
            delay=interval,
            event_type=EventType.INTERVAL,
            priority=priority,
            repeat=repeat,
        )

    def schedule_condition(
        self,
        callback: Callable[..., Any],
        condition: Callable[[], bool],
        check_interval: float = 1.0,
        priority: int = 0,
    ) -> str:
        """安排条件事件.

        Args:
            callback: 回调函数
            condition: 条件函数
            check_interval: 检查间隔
            priority: 优先级

        Returns:
            事件ID
        """
        return self.schedule(
            callback=callback,
            delay=check_interval,
            event_type=EventType.CONDITION,
            condition=condition,
            priority=priority,
        )

    def schedule_frame(
        self,
        callback: Callable[..., Any],
        priority: int = 0,
    ) -> str:
        """安排帧事件.

        Args:
            callback: 回调函数
            priority: 优先级

        Returns:
            事件ID
        """
        return self.schedule(
            callback=callback,
            event_type=EventType.FRAME,
            priority=priority,
        )

    def cancel(self, event_id: str) -> bool:
        """取消事件.

        Args:
            event_id: 事件ID

        Returns:
            是否成功取消
        """
        # 标记为已取消
        self._cancelled_events.add(event_id)

        # 检查队列中是否存在
        for _i, (_, _, event) in enumerate(self._queue):
            if event.id == event_id:
                logger.debug(f"取消事件: id={event_id}")
                return True

        # 检查帧事件
        for i, event in enumerate(self._frame_events):
            if event.id == event_id:
                self._frame_events.pop(i)
                logger.debug(f"取消帧事件: id={event_id}")
                return True

        return False

    async def run(self) -> None:
        """运行调度器主循环."""
        self._running = True
        logger.info("事件调度器已启动")

        try:
            while self._running:
                current_time = time.time()

                # 处理普通事件队列
                while self._queue:
                    exec_time, _, event = self._queue[0]

                    # 检查是否已取消
                    if event.id in self._cancelled_events:
                        heapq.heappop(self._queue)
                        self._cancelled_events.discard(event.id)
                        continue

                    # 检查是否到达执行时间
                    if exec_time > current_time:
                        break

                    # 取出并执行事件
                    heapq.heappop(self._queue)
                    await self._execute_event(event)

                # 处理帧事件
                for event in self._frame_events[:]:
                    if event.id in self._cancelled_events:
                        self._frame_events.remove(event)
                        self._cancelled_events.discard(event.id)
                        continue

                    await self._execute_frame_event(event)

                # 等待一小段时间
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            logger.info("事件调度器已取消")
        except Exception:
            logger.exception("事件调度器异常")
        finally:
            self._running = False

    async def _execute_event(self, event: Event) -> None:
        """执行单个事件.

        Args:
            event: 事件定义
        """
        try:
            if event.event_type == EventType.CONDITION:
                # 条件事件
                if event.condition and event.condition():
                    await event.callback()
                    # 重新安排（一次性条件事件）
                    if event.repeat != 1:
                        self.schedule(
                            callback=event.callback,
                            delay=event.delay,
                            event_type=event.event_type,
                            condition=event.condition,
                            priority=event.priority,
                            repeat=event.repeat - 1 if event.repeat > 0 else 0,
                        )
            else:
                # 普通事件
                await event.callback()

                # 重新安排周期事件
                if event.event_type == EventType.INTERVAL and event.repeat != 1:
                    new_repeat = event.repeat - 1 if event.repeat > 0 else 0
                    self.schedule(
                        callback=event.callback,
                        delay=event.delay,
                        event_type=event.event_type,
                        priority=event.priority,
                        repeat=new_repeat,
                    )

        except Exception:
            # 记录错误但继续运行
            logger.exception(f"事件执行错误: id={event.id}")

    async def _execute_frame_event(self, event: Event) -> None:
        """执行帧事件.

        Args:
            event: 事件定义
        """
        try:
            await event.callback()
        except Exception:
            logger.exception(f"帧事件执行错误: id={event.id}")

    def start(self) -> None:
        """启动调度器."""
        if self._running:
            return

        self._task = asyncio.create_task(self.run())
        logger.info("事件调度器启动中...")

    def stop(self) -> None:
        """停止调度器."""
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()

        logger.info("事件调度器已停止")

    def is_running(self) -> bool:
        """检查是否运行中.

        Returns:
            是否运行中
        """
        return self._running

    def get_stats(self) -> dict[str, Any]:
        """获取调度器统计信息.

        Returns:
            统计信息字典
        """
        return {
            "queue_size": len(self._queue),
            "frame_events": len(self._frame_events),
            "time_scale": self._time_scale,
            "running": self._running,
        }

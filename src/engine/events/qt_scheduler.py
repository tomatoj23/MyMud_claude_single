"""Qt 兼容的事件调度器.

基于 QTimer 实现，与 PySide6 事件循环兼容。
保留原调度器 API，但内部使用可插拔后端。
"""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from collections.abc import Callable
from typing import Any

from src.utils.logging import get_logger
from .scheduler import EventScheduler, Event, EventType
from .backends import SchedulerBackend, HybridBackend, create_backend

logger = get_logger(__name__)


class FlexibleEventScheduler(EventScheduler):
    """灵活的事件调度器.
    
    支持 asyncio 和 Qt 两种后端，可配置选择。
    与原 EventScheduler 完全兼容的 API。
    """
    
    def __init__(self, backend: str | SchedulerBackend = "hybrid"):
        """初始化灵活调度器.
        
        Args:
            backend: 后端类型或后端实例 ("asyncio", "qt", "hybrid")
        """
        super().__init__()
        
        # 后端实例
        if isinstance(backend, str):
            self._backend = create_backend(backend)
        else:
            self._backend = backend
        
        # 存储事件ID到后端句柄的映射
        self._handles: dict[str, Any] = {}
        
        # 帧事件（需要特殊处理）
        self._frame_timer = None
    
    @property
    def backend_type(self) -> str:
        """获取后端类型."""
        if hasattr(self._backend, 'backend_type'):
            return self._backend.backend_type
        return type(self._backend).__name__.lower().replace('backend', '')
    
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
        
        重写父类方法，使用后端调度。
        """
        # 生成事件ID
        event_id = str(uuid.uuid4())
        
        # 创建事件对象（保持兼容性）
        event = Event(
            id=event_id,
            event_type=event_type,
            callback=callback,
            delay=delay,
            condition=condition,
            priority=priority,
            repeat=repeat,
        )
        
        # 根据事件类型选择调度方式
        if event_type == EventType.FRAME:
            # 帧事件使用特殊处理
            self._frame_events.append(event)
            self._start_frame_timer()
        elif event_type == EventType.DELAY:
            # 延迟事件
            handle = self._backend.schedule(
                delay / self._time_scale,
                self._wrap_callback(callback, event_id)
            )
            self._handles[event_id] = handle
        elif event_type == EventType.INTERVAL:
            # 周期事件
            if repeat == 0:
                # 无限重复
                handle = self._backend.schedule_interval(
                    delay / self._time_scale,
                    self._wrap_callback(callback, event_id)
                )
                self._handles[event_id] = handle
            else:
                # 有限重复 - 使用延迟事件模拟
                self._schedule_limited_repeat(event, repeat)
        elif event_type == EventType.CONDITION:
            # 条件事件 - 需要轮询检查
            self._schedule_condition(event)
        
        logger.debug(f"安排事件: id={event_id}, type={event_type.name}, delay={delay}")
        return event_id
    
    def _wrap_callback(self, callback: Callable[..., Any], event_id: str) -> Callable:
        """包装回调函数，添加错误处理和状态管理."""
        async def wrapped():
            if event_id in self._cancelled_events:
                return
            
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.exception(f"事件执行错误: {e}")
            finally:
                # 清理句柄（如果是一次性事件）
                if event_id in self._handles:
                    del self._handles[event_id]
        
        return wrapped
    
    def _schedule_limited_repeat(self, event: Event, repeat: int) -> None:
        """调度有限重复事件."""
        count = [0]  # 使用列表实现闭包
        
        async def repeated_callback():
            if event.id in self._cancelled_events:
                return
            
            count[0] += 1
            
            try:
                if inspect.iscoroutinefunction(event.callback):
                    await event.callback()
                else:
                    event.callback()
            except Exception as e:
                logger.exception(f"周期事件执行错误: {e}")
            
            # 检查是否达到重复次数
            if count[0] >= repeat:
                self._cancelled_events.add(event.id)
                if event.id in self._handles:
                    del self._handles[event.id]
        
        handle = self._backend.schedule_interval(
            event.delay / self._time_scale,
            repeated_callback
        )
        self._handles[event.id] = handle
    
    def _schedule_condition(self, event: Event) -> None:
        """调度条件事件."""
        async def condition_checker():
            if event.id in self._cancelled_events:
                return
            
            # 检查条件
            if event.condition and event.condition():
                try:
                    if inspect.iscoroutinefunction(event.callback):
                        await event.callback()
                    else:
                        event.callback()
                except Exception as e:
                    logger.exception(f"条件事件执行错误: {e}")
                
                # 条件满足后取消（如果需要）
                if event.repeat == 0:
                    self._cancelled_events.add(event.id)
                    if event.id in self._handles:
                        del self._handles[event.id]
                    return
            
            # 重新调度检查
            if event.id not in self._cancelled_events:
                handle = self._backend.schedule(
                    event.delay / self._time_scale,
                    condition_checker
                )
                self._handles[event.id] = handle
        
        # 首次调度
        handle = self._backend.schedule(
            event.delay / self._time_scale,
            condition_checker
        )
        self._handles[event.id] = handle
    
    def _start_frame_timer(self) -> None:
        """启动帧定时器."""
        if self._frame_timer is not None:
            return
        
        try:
            from PySide6.QtCore import QTimer
            self._frame_timer = QTimer()
            self._frame_timer.timeout.connect(self._process_frame_events)
            self._frame_timer.start(16)  # ~60 FPS
        except ImportError:
            # 使用 asyncio 模拟
            import asyncio
            self._frame_timer = asyncio.create_task(self._frame_loop())
    
    async def _frame_loop(self) -> None:
        """帧事件循环（asyncio 模式）."""
        while self._running:
            await self._process_frame_events()
            await asyncio.sleep(0.016)  # ~60 FPS
    
    async def _process_frame_events(self) -> None:
        """处理帧事件."""
        for event in self._frame_events[:]:
            if event.id in self._cancelled_events:
                self._frame_events.remove(event)
                self._cancelled_events.discard(event.id)
                continue
            
            try:
                if inspect.iscoroutinefunction(event.callback):
                    await event.callback()
                else:
                    event.callback()
            except Exception as e:
                logger.exception(f"帧事件执行错误: {e}")
    
    def cancel(self, event_id: str) -> bool:
        """取消事件."""
        # 调用父类方法
        result = super().cancel(event_id)
        
        # 取消后端任务
        if event_id in self._handles:
            handle = self._handles.pop(event_id)
            self._backend.cancel(handle)
        
        return result
    
    async def start(self) -> None:
        """启动调度器."""
        self._running = True
        await self._backend.start()
        logger.info(f"灵活调度器已启动 (后端: {self.backend_type})")
    
    async def stop(self) -> None:
        """停止调度器."""
        self._running = False
        
        # 取消所有后端任务
        for handle in self._handles.values():
            self._backend.cancel(handle)
        self._handles.clear()
        
        # 停止帧定时器
        if self._frame_timer:
            try:
                from PySide6.QtCore import QTimer
                if isinstance(self._frame_timer, QTimer):
                    self._frame_timer.stop()
                    self._frame_timer.deleteLater()
            except ImportError:
                if hasattr(self._frame_timer, 'cancel'):
                    self._frame_timer.cancel()
            self._frame_timer = None
        
        await self._backend.stop()
        logger.info("灵活调度器已停止")
    
    async def run(self) -> None:
        """运行调度器主循环."""
        # 如果使用 Qt 后端，不需要手动运行循环
        # Qt 的事件循环会处理一切
        if self.backend_type == "qt":
            logger.info("Qt 后端：依赖 Qt 事件循环，无需手动运行")
            # 保持运行状态
            while self._running:
                await asyncio.sleep(0.1)
        else:
            # 使用父类的实现
            await super().run()


# 向后兼容：EventScheduler 现在是 FlexibleEventScheduler 的别名
EventScheduler = FlexibleEventScheduler

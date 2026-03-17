"""事件调度器后端 - 支持不同的事件循环实现.

提供 asyncio 和 Qt (PySide6) 两种后端实现。
"""
from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SchedulerBackend(ABC):
    """调度器后端抽象基类."""
    
    @abstractmethod
    def schedule(
        self,
        delay: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """调度延迟任务.
        
        Args:
            delay: 延迟时间（秒）
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务句柄
        """
        pass
    
    @abstractmethod
    def schedule_interval(
        self,
        interval: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """调度周期任务.
        
        Args:
            interval: 间隔时间（秒）
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务句柄
        """
        pass
    
    @abstractmethod
    def cancel(self, handle: Any) -> bool:
        """取消任务.
        
        Args:
            handle: 任务句柄
            
        Returns:
            是否成功取消
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """检查是否运行中."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """启动后端."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止后端."""
        pass


class AsyncioBackend(SchedulerBackend):
    """asyncio 后端实现.
    
    使用 asyncio 的 create_task 和 sleep。
    """
    
    def __init__(self):
        """初始化 asyncio 后端."""
        self._tasks: set[asyncio.Task] = set()
        self._running = False
    
    def schedule(
        self,
        delay: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Task:
        """调度延迟任务."""
        async def delayed_task():
            await asyncio.sleep(delay)
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.exception(f"延迟任务执行错误: {e}")
        
        task = asyncio.create_task(delayed_task())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    def schedule_interval(
        self,
        interval: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Task:
        """调度周期任务."""
        async def interval_task():
            while True:
                await asyncio.sleep(interval)
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    logger.exception(f"周期任务执行错误: {e}")
        
        task = asyncio.create_task(interval_task())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    def cancel(self, handle: asyncio.Task) -> bool:
        """取消任务."""
        if handle and not handle.done():
            handle.cancel()
            return True
        return False
    
    def is_running(self) -> bool:
        """检查是否运行中."""
        return self._running
    
    async def start(self) -> None:
        """启动后端."""
        self._running = True
        logger.info("Asyncio 后端已启动")
    
    async def stop(self) -> None:
        """停止后端."""
        self._running = False
        # 取消所有任务
        for task in list(self._tasks):
            task.cancel()
        logger.info("Asyncio 后端已停止")


class QtBackend(SchedulerBackend):
    """Qt (PySide6) 后端实现.
    
    使用 QTimer 实现，与 Qt 事件循环兼容。
    """
    
    def __init__(self):
        """初始化 Qt 后端."""
        self._timers: dict[int, Any] = {}  # id -> QTimer
        self._timer_id = 0
        self._running = False
        self._qtimer_class = None
        self._qt_core = None
    
    def _get_qtimer(self):
        """获取 QTimer 类（延迟导入）."""
        if self._qtimer_class is None:
            try:
                from PySide6.QtCore import QTimer
                self._qtimer_class = QTimer
            except ImportError:
                raise ImportError("PySide6 未安装，无法使用 Qt 后端")
        return self._qtimer_class
    
    def schedule(
        self,
        delay: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> int:
        """调度延迟任务."""
        QTimer = self._get_qtimer()
        
        timer = QTimer()
        timer.setSingleShot(True)
        
        def on_timeout():
            try:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(*args, **kwargs))
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Qt 延迟任务执行错误: {e}")
        
        timer.timeout.connect(on_timeout)
        timer.start(int(delay * 1000))  # 转换为毫秒
        
        self._timer_id += 1
        self._timers[self._timer_id] = timer
        return self._timer_id
    
    def schedule_interval(
        self,
        interval: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> int:
        """调度周期任务."""
        QTimer = self._get_qtimer()
        
        timer = QTimer()
        timer.setSingleShot(False)
        
        def on_timeout():
            try:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(*args, **kwargs))
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Qt 周期任务执行错误: {e}")
        
        timer.timeout.connect(on_timeout)
        timer.start(int(interval * 1000))  # 转换为毫秒
        
        self._timer_id += 1
        self._timers[self._timer_id] = timer
        return self._timer_id
    
    def cancel(self, handle: int) -> bool:
        """取消任务."""
        if handle in self._timers:
            timer = self._timers.pop(handle)
            timer.stop()
            timer.deleteLater()
            return True
        return False
    
    def is_running(self) -> bool:
        """检查是否运行中."""
        return self._running
    
    async def start(self) -> None:
        """启动后端."""
        self._running = True
        logger.info("Qt 后端已启动")
    
    async def stop(self) -> None:
        """停止后端."""
        self._running = False
        # 停止所有定时器
        for timer in self._timers.values():
            timer.stop()
            timer.deleteLater()
        self._timers.clear()
        logger.info("Qt 后端已停止")


class HybridBackend(SchedulerBackend):
    """混合后端 - 自动检测并使用可用的后端.
    
    优先使用 Qt 后端（如果 PySide6 可用），否则使用 asyncio 后端。
    """
    
    def __init__(self):
        """初始化混合后端."""
        self._backend: SchedulerBackend | None = None
        self._backend_type: str = "none"
    
    def _init_backend(self) -> SchedulerBackend:
        """初始化后端."""
        if self._backend is not None:
            return self._backend
        
        # 尝试 Qt 后端
        try:
            self._backend = QtBackend()
            self._backend_type = "qt"
            logger.info("使用 Qt 后端")
            return self._backend
        except ImportError:
            pass
        
        # 使用 asyncio 后端
        self._backend = AsyncioBackend()
        self._backend_type = "asyncio"
        logger.info("使用 asyncio 后端")
        return self._backend
    
    @property
    def backend_type(self) -> str:
        """获取后端类型."""
        return self._backend_type
    
    def schedule(
        self,
        delay: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """调度延迟任务."""
        return self._init_backend().schedule(delay, callback, *args, **kwargs)
    
    def schedule_interval(
        self,
        interval: float,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """调度周期任务."""
        return self._init_backend().schedule_interval(interval, callback, *args, **kwargs)
    
    def cancel(self, handle: Any) -> bool:
        """取消任务."""
        if self._backend:
            return self._backend.cancel(handle)
        return False
    
    def is_running(self) -> bool:
        """检查是否运行中."""
        if self._backend:
            return self._backend.is_running()
        return False
    
    async def start(self) -> None:
        """启动后端."""
        await self._init_backend().start()
    
    async def stop(self) -> None:
        """停止后端."""
        if self._backend:
            await self._backend.stop()


def create_backend(backend_type: str = "hybrid") -> SchedulerBackend:
    """创建调度器后端.
    
    Args:
        backend_type: 后端类型 ("asyncio", "qt", "hybrid")
        
    Returns:
        调度器后端实例
    """
    if backend_type == "asyncio":
        return AsyncioBackend()
    elif backend_type == "qt":
        return QtBackend()
    elif backend_type == "hybrid":
        return HybridBackend()
    else:
        raise ValueError(f"未知的后端类型: {backend_type}")

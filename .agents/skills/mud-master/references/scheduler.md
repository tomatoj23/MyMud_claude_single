# EventScheduler实现指南

## 核心概念

EventScheduler管理游戏中的所有时间相关事件：

1. **延迟事件** - 指定时间后执行
2. **周期事件** - 按固定间隔重复执行
3. **条件事件** - 满足条件时执行
4. **帧事件** - 每帧执行

## 实现要点

### 1. 事件类型定义

```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Any
import asyncio


class EventType(Enum):
    DELAY = auto()      # 延迟执行
    INTERVAL = auto()   # 周期执行
    CONDITION = auto()  # 条件执行
    FRAME = auto()      # 每帧执行


@dataclass
class Event:
    """事件定义。"""
    id: str
    event_type: EventType
    callback: Callable[..., Any]
    delay: float = 0.0          # 延迟/间隔时间（秒）
    condition: Callable[[], bool] = None  # 条件函数
    priority: int = 0           # 优先级（越小越高）
    repeat: int = 0             # 重复次数（0表示无限）
```

### 2. 调度器实现

```python
import heapq
import time


class EventScheduler:
    """事件调度器。
    
    使用asyncio和优先队列管理事件。
    """
    
    def __init__(self) -> None:
        self._queue: list[tuple[float, int, Event]] = []
        self._time_scale = 1.0
        self._running = False
        self._task: asyncio.Task | None = None
    
    def set_time_scale(self, scale: float) -> None:
        """设置时间膨胀系数。
        
        Args:
            scale: 时间系数（1.0为正常，0.5为一半速度）
        """
        self._time_scale = scale
    
    def schedule(self, event: Event) -> None:
        """安排事件。
        
        Args:
            event: 事件定义
        """
        exec_time = time.time() + event.delay / self._time_scale
        heapq.heappush(self._queue, (exec_time, event.priority, event))
    
    def cancel(self, event_id: str) -> bool:
        """取消事件。
        
        Args:
            event_id: 事件ID
            
        Returns:
            是否成功取消
        """
        for i, (_, _, event) in enumerate(self._queue):
            if event.id == event_id:
                self._queue.pop(i)
                heapq.heapify(self._queue)
                return True
        return False
    
    async def run(self) -> None:
        """运行调度器主循环。"""
        self._running = True
        while self._running:
            if self._queue:
                exec_time, _, event = self._queue[0]
                wait_time = exec_time - time.time()
                
                if wait_time <= 0:
                    # 执行事件
                    heapq.heappop(self._queue)
                    await self._execute_event(event)
                else:
                    # 等待
                    await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.01)
    
    async def _execute_event(self, event: Event) -> None:
        """执行单个事件。"""
        try:
            if event.event_type == EventType.CONDITION:
                if event.condition and event.condition():
                    await event.callback()
                    if event.repeat != 1:
                        self.schedule(event)
            else:
                await event.callback()
                
                # 重新安排周期事件
                if event.event_type == EventType.INTERVAL and event.repeat != 1:
                    event.repeat -= 1 if event.repeat > 0 else 0
                    self.schedule(event)
        except Exception as e:
            # 记录错误但继续运行
            print(f"Event {event.id} error: {e}")
    
    def stop(self) -> None:
        """停止调度器。"""
        self._running = False
```

## 注意事项

1. 回调函数必须是异步的（async def）
2. 事件ID应唯一，避免重复
3. 时间膨胀只影响延迟/周期事件，不影响帧事件
4. 异常处理确保单个事件失败不影响其他事件

---

# Qt 兼容调度器

## 问题

原始调度器使用 `asyncio.sleep()` 运行在自己的循环中，与 PySide6 的 Qt 事件循环冲突，会导致 GUI 卡顿。

## 解决方案

使用可插拔后端设计，支持 asyncio 和 Qt 两种实现：

```python
# 自动检测并使用 Qt 后端（如果 PySide6 可用）
from src.engine.events.qt_scheduler import FlexibleEventScheduler

scheduler = FlexibleEventScheduler("hybrid")  # 自动选择
# 或明确指定
scheduler = FlexibleEventScheduler("qt")       # Qt 后端
scheduler = FlexibleEventScheduler("asyncio")  # asyncio 后端
```

## 后端类型

| 后端 | 适用场景 | 特点 |
|:---|:---|:---|
| `asyncio` | 纯命令行/服务器 | 标准 asyncio |
| `qt` | PySide6 GUI | 使用 QTimer，与 Qt 事件循环兼容 |
| `hybrid` | 自动检测 | 优先使用 Qt 后端 |

## 使用方式

与原始调度器完全兼容的 API：

```python
# 创建调度器
scheduler = FlexibleEventScheduler("qt")

# 安排延迟事件
event_id = scheduler.schedule_delay(
    callback=my_callback,
    delay=5.0
)

# 安排周期事件
event_id = scheduler.schedule_interval(
    callback=my_callback,
    interval=1.0
)

# 取消事件
scheduler.cancel(event_id)

# 启动/停止
await scheduler.start()
await scheduler.stop()
```

## Qt 后端实现

```python
class QtBackend(SchedulerBackend):
    """Qt (PySide6) 后端实现"""
    
    def schedule(self, delay: float, callback: Callable, *args, **kwargs):
        """使用 QTimer 调度延迟任务"""
        from PySide6.QtCore import QTimer
        
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: asyncio.create_task(callback(*args, **kwargs)))
        timer.start(int(delay * 1000))  # 毫秒
        return timer
    
    def schedule_interval(self, interval: float, callback: Callable, *args, **kwargs):
        """使用 QTimer 调度周期任务"""
        from PySide6.QtCore import QTimer
        
        timer = QTimer()
        timer.setSingleShot(False)
        timer.timeout.connect(lambda: asyncio.create_task(callback(*args, **kwargs)))
        timer.start(int(interval * 1000))
        return timer
```

## 与 GameEngine 集成

```python
from src.engine.core.engine import GameEngine
from src.engine.events.qt_scheduler import FlexibleEventScheduler

# 创建带 Qt 调度器的引擎
engine = GameEngine(config)
engine._events = FlexibleEventScheduler("qt")

# 启动引擎
await engine.initialize()
await engine.start()
```

## 注意事项

1. **Qt 后端依赖 PySide6** - 需要安装 PySide6
2. **帧事件使用 QTimer** - 默认 60 FPS (16ms 间隔)
3. **与 Qt 信号兼容** - 可以在事件回调中发射 Qt 信号
4. **同一线程** - 调度器和 GUI 应在同一线程运行

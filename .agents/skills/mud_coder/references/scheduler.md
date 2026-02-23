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

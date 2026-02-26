# 性能监控系统设计文档

> 金庸武侠MUD项目 - 轻量级运行时性能监控方案

**文档版本**: 1.0  
**设计日期**: 2026-02-26  
**状态**: 待评审  
**优先级**: 建议实施 (对阶段4 GUI和阶段6开发者模式有直接价值)

---

## 1. 背景与目标

### 1.1 当前痛点

```
┌─────────────────────────────────────────────────────────────┐
│  现状：被动查询，无法实时感知                                │
├─────────────────────────────────────────────────────────────┤
│  ❌ 无法知道命令执行耗时分布                                 │
│  ❌ 无法检测慢查询（>100ms）                                │
│  ❌ 无法监控缓存命中率趋势                                   │
│  ❌ 内存泄漏需人工排查                                       │
│  ❌ 性能问题发现滞后                                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计目标

| 目标 | 描述 | 验收标准 |
|:---|:---|:---|
| **可观测** | 核心操作全链路可追踪 | 命令/DB/缓存/API全覆盖 |
| **低开销** | 监控本身不成为性能瓶颈 | <1% CPU，<10MB内存 |
| **易集成** | 对现有代码侵入性最小 | 装饰器/上下文管理器 |
| **可导出** | 数据可被GUI/外部工具消费 | JSON/实时流接口 |
| **可配置** | 支持开发/生产不同策略 | 采样率/级别控制 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        性能监控架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐        ┌──────────────────┐              │
│  │   数据收集层      │───────▶│   数据存储层      │              │
│  │  (Instrumentation)│       │   (Ring Buffer)  │              │
│  └──────────────────┘        └────────┬─────────┘              │
│           │                           │                         │
│           ▼                           ▼                         │
│  ┌──────────────────┐        ┌──────────────────┐              │
│  │ • @timed 装饰器   │        │ • Metrics存储    │              │
│  │ • span 上下文     │        │ • Histogram      │              │
│  │ • counter 计数    │        │ • Counter        │              │
│  │ • gauge 瞬时值    │        │ • Gauge          │              │
│  └──────────────────┘        └────────┬─────────┘              │
│                                       │                         │
│                                       ▼                         │
│                              ┌──────────────────┐              │
│                              │   数据查询层      │              │
│                              │   (Query API)    │              │
│                              └────────┬─────────┘              │
│                                       │                         │
│                    ┌──────────────────┼──────────────────┐     │
│                    ▼                  ▼                  ▼     │
│           ┌─────────────┐   ┌─────────────┐   ┌─────────────┐ │
│           │  实时展示    │   │  性能报告   │   │  告警通知   │ │
│           │  (GUI面板)  │   │  (导出)     │   │  (阈值)     │ │
│           └─────────────┘   └─────────────┘   └─────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 文件位置 |
|:---|:---|:---|
| `Metric` | 数据模型（名称/值/时间戳/标签） | `src/utils/performance.py` |
| `PerformanceMonitor` | 核心监控器（单例） | `src/utils/performance.py` |
| `@timed` | 耗时统计装饰器 | `src/utils/performance_hooks.py` |
| `@counted` | 计数装饰器 | `src/utils/performance_hooks.py` |
| `span()` | 上下文管理器 | `src/utils/performance_hooks.py` |

---

## 3. 详细设计

### 3.1 数据模型

```python
# src/utils/performance.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class MetricType(Enum):
    """指标类型."""
    COUNTER = auto()    # 累加计数（如总请求数）
    GAUGE = auto()      # 瞬时值（如当前内存）
    HISTOGRAM = auto()  # 分布统计（如响应时间）
    SPAN = auto()       # 跨度追踪（如完整请求链路）


@dataclass(frozen=True)
class Metric:
    """单个指标数据点.
    
    Attributes:
        name: 指标名称（如"command.duration"）
        value: 数值（单位取决于指标）
        timestamp: 采集时间戳
        metric_type: 指标类型
        tags: 标签（用于分组过滤）
    """
    name: str
    value: float
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metric_type: MetricType = MetricType.GAUGE
    tags: dict[str, str] = field(default_factory=dict)
    
    def with_tag(self, key: str, value: str) -> "Metric":
        """添加标签（函数式）."""
        new_tags = {**self.tags, key: value}
        return Metric(
            name=self.name,
            value=self.value,
            timestamp=self.timestamp,
            metric_type=self.metric_type,
            tags=new_tags
        )


@dataclass
class HistogramSnapshot:
    """直方图统计快照."""
    count: int          # 样本数
    sum: float          # 总和
    min: float          # 最小值
    max: float          # 最大值
    avg: float          # 平均值
    p50: float          # 中位数
    p95: float          # 95分位数
    p99: float          # 99分位数
```

### 3.2 核心监控器

```python
# src/utils/performance.py

import time
import threading
from collections import deque
from typing import Callable


class PerformanceMonitor:
    """性能监控器 - 线程安全的单例.
    
    使用环形缓冲区存储指标，避免内存无限增长。
    
    Example:
        >>> monitor = get_performance_monitor()
        >>> monitor.record(Metric("db.query", 12.5, tags={"table": "objects"}))
        >>> stats = monitor.get_histogram("db.query")
    """
    
    _instance: "PerformanceMonitor | None" = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "PerformanceMonitor":
        """单例模式."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        max_metrics: int = 10000,
        histogram_buckets: int = 1000,
        enabled: bool = True
    ) -> None:
        """初始化监控器.
        
        Args:
            max_metrics: 环形缓冲区大小
            histogram_buckets: 每个直方图保留的样本数
            enabled: 是否启用监控
        """
        if self._initialized:
            return
            
        self._enabled = enabled
        self._max_metrics = max_metrics
        self._histogram_buckets = histogram_buckets
        
        # 线程安全的指标存储
        self._metrics: deque[Metric] = deque(maxlen=max_metrics)
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, deque[float]] = {}
        
        # 配置
        self._sampling_rate = 1.0  # 采样率（1.0 = 100%）
        self._slow_threshold_ms = 100  # 慢操作阈值
        
        self._initialized = True
        self._lock = threading.Lock()
    
    # ==================== 核心API ====================
    
    def record(self, metric: Metric) -> None:
        """记录单个指标.
        
        根据metric_type自动路由到对应存储。
        """
        if not self._enabled:
            return
            
        # 采样控制
        if self._sampling_rate < 1.0:
            if hash(metric.name) % 100 > int(self._sampling_rate * 100):
                return
        
        with self._lock:
            if metric.metric_type == MetricType.COUNTER:
                self._counters[metric.name] = self._counters.get(metric.name, 0) + int(metric.value)
            elif metric.metric_type == MetricType.GAUGE:
                self._gauges[metric.name] = metric.value
            elif metric.metric_type == MetricType.HISTOGRAM:
                if metric.name not in self._histograms:
                    self._histograms[metric.name] = deque(maxlen=self._histogram_buckets)
                self._histograms[metric.name].append(metric.value)
            
            # 所有指标都存入时间序列（用于追踪）
            self._metrics.append(metric)
    
    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """快捷方法：计数器+1."""
        self.record(Metric(
            name=name,
            value=float(value),
            metric_type=MetricType.COUNTER,
            tags=tags or {}
        ))
    
    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """快捷方法：设置瞬时值."""
        self.record(Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            tags=tags or {}
        ))
    
    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """快捷方法：记录直方图样本."""
        self.record(Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            tags=tags or {}
        ))
    
    # ==================== 查询API ====================
    
    def get_counter(self, name: str) -> int:
        """获取计数器当前值."""
        with self._lock:
            return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float | None:
        """获取瞬时值."""
        with self._lock:
            return self._gauges.get(name)
    
    def get_histogram(self, name: str) -> HistogramSnapshot | None:
        """获取直方图统计快照."""
        with self._lock:
            samples = list(self._histograms.get(name, []))
        
        if not samples:
            return None
            
        samples.sort()
        n = len(samples)
        
        return HistogramSnapshot(
            count=n,
            sum=sum(samples),
            min=samples[0],
            max=samples[-1],
            avg=sum(samples) / n,
            p50=samples[n // 2],
            p95=samples[int(n * 0.95)],
            p99=samples[int(n * 0.99)]
        )
    
    def query(
        self,
        name_pattern: str | None = None,
        tags_filter: dict[str, str] | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100
    ) -> list[Metric]:
        """查询指标时间序列.
        
        支持按名称通配符、标签、时间范围过滤。
        """
        results = []
        with self._lock:
            metrics_copy = list(self._metrics)
        
        for metric in reversed(metrics_copy):  # 最新优先
            if len(results) >= limit:
                break
                
            if name_pattern and not self._match_pattern(metric.name, name_pattern):
                continue
                
            if tags_filter:
                if not all(metric.tags.get(k) == v for k, v in tags_filter.items()):
                    continue
                    
            if start_time and metric.timestamp < start_time:
                continue
                
            if end_time and metric.timestamp > end_time:
                continue
                
            results.append(metric)
            
        return results
    
    def get_all_stats(self) -> dict[str, Any]:
        """获取所有统计信息（用于导出）."""
        with self._lock:
            histogram_stats = {
                name: self._calc_histogram_stats(samples)
                for name, samples in self._histograms.items()
            }
            
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
                "total_metrics": len(self._metrics),
                "config": {
                    "max_metrics": self._max_metrics,
                    "sampling_rate": self._sampling_rate,
                    "enabled": self._enabled
                }
            }
    
    # ==================== 配置管理 ====================
    
    def set_sampling_rate(self, rate: float) -> None:
        """设置采样率（0.0-1.0）."""
        self._sampling_rate = max(0.0, min(1.0, rate))
    
    def set_slow_threshold(self, ms: int) -> None:
        """设置慢操作阈值（毫秒）."""
        self._slow_threshold_ms = ms
    
    def reset(self) -> None:
        """重置所有数据（测试用）."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
    
    # ==================== 内部方法 ====================
    
    def _match_pattern(self, name: str, pattern: str) -> bool:
        """简单的通配符匹配（* 匹配任意字符）."""
        if "*" not in pattern:
            return name == pattern
        # 简化的通配符匹配
        parts = pattern.split("*")
        if name.startswith(parts[0]):
            remaining = name[len(parts[0]):]
            for part in parts[1:]:
                if part not in remaining:
                    return False
                remaining = remaining[remaining.index(part) + len(part):]
            return True
        return False
    
    def _calc_histogram_stats(self, samples: deque[float]) -> dict[str, float]:
        """计算直方图统计."""
        if not samples:
            return {}
        sorted_samples = sorted(samples)
        n = len(sorted_samples)
        return {
            "count": n,
            "avg": sum(sorted_samples) / n,
            "min": sorted_samples[0],
            "max": sorted_samples[-1],
            "p95": sorted_samples[int(n * 0.95)] if n >= 20 else sorted_samples[-1]
        }


# 全局实例
def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例."""
    return PerformanceMonitor()
```

### 3.3 装饰器和上下文管理器

```python
# src/utils/performance_hooks.py

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

from src.utils.performance import Metric, MetricType, get_performance_monitor
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def timed(
    metric_name: str | None = None,
    tags: dict[str, str] | None = None,
    log_slow: bool = True
) -> Callable[[F], F]:
    """函数执行时间监控装饰器.
    
    支持同步和异步函数。
    
    Args:
        metric_name: 指标名称（默认使用函数名）
        tags: 额外标签
        log_slow: 是否记录慢操作日志
        
    Example:
        >>> @timed("db.query", tags={"table": "objects"})
        ... async def fetch_objects():
        ...     return await db.fetchall("SELECT * FROM objects")
    """
    def decorator(func: F) -> F:
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = get_performance_monitor()
            start = time.perf_counter()
            
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                monitor.histogram(name, duration_ms, tags)
                
                # 慢操作告警
                if log_slow and duration_ms > monitor._slow_threshold_ms:
                    logger.warning(
                        f"Slow operation detected: {name} took {duration_ms:.2f}ms",
                        extra={"metric": name, "duration_ms": duration_ms, "tags": tags}
                    )
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = get_performance_monitor()
            start = time.perf_counter()
            
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                monitor.histogram(name, duration_ms, tags)
                
                if log_slow and duration_ms > monitor._slow_threshold_ms:
                    logger.warning(
                        f"Slow operation detected: {name} took {duration_ms:.2f}ms",
                        extra={"metric": name, "duration_ms": duration_ms, "tags": tags}
                    )
        
        # 根据函数类型返回对应包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def counted(
    metric_name: str | None = None,
    tags: dict[str, str] | None = None
) -> Callable[[F], F]:
    """函数调用次数监控装饰器.
    
    Example:
        >>> @counted("command.executed", tags={"cmd": "look"})
        ... async def handle_look(caller, args):
        ...     pass
    """
    def decorator(func: F) -> F:
        name = metric_name or f"call_count.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = get_performance_monitor()
            monitor.increment(name, tags=tags)
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = get_performance_monitor()
            monitor.increment(name, tags=tags)
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


@contextmanager
def span(
    operation_name: str,
    tags: dict[str, str] | None = None,
    monitor=None
):
    """跨度追踪上下文管理器.
    
    用于追踪一段代码块的执行时间和状态。
    
    Args:
        operation_name: 操作名称
        tags: 标签
        monitor: 指定监控器（默认全局）
        
    Example:
        >>> with span("combat.round", tags={"round": 1}):
        ...     await process_combat_round()
    """
    mon = monitor or get_performance_monitor()
    start = time.perf_counter()
    
    try:
        yield mon
    except Exception as e:
        # 记录错误
        mon.increment(f"{operation_name}.errors", tags={**(tags or {}), "error": type(e).__name__})
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        mon.histogram(operation_name, duration_ms, tags)


class Timer:
    """手动计时器（用于复杂场景）.
    
    Example:
        >>> timer = Timer("custom.operation")
        >>> timer.start()
        >>> # ... 执行操作
        >>> timer.stop()  # 自动记录
    """
    
    def __init__(self, name: str, tags: dict[str, str] | None = None):
        self.name = name
        self.tags = tags or {}
        self._start_time: float | None = None
        self._duration_ms: float | None = None
    
    def start(self) -> "Timer":
        """开始计时."""
        self._start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """停止计时并记录."""
        if self._start_time is None:
            raise RuntimeError("Timer not started")
        
        self._duration_ms = (time.perf_counter() - self._start_time) * 1000
        get_performance_monitor().histogram(self.name, self._duration_ms, self.tags)
        return self._duration_ms
    
    @property
    def duration_ms(self) -> float | None:
        """获取耗时（毫秒）."""
        return self._duration_ms
```

---

## 4. 系统集成方案

### 4.1 引擎集成

```python
# src/engine/core/engine.py

from src.utils.performance import get_performance_monitor
from src.utils.performance_hooks import span

class GameEngine:
    def __init__(self, ...):
        # ... 现有初始化代码 ...
        self._monitor = get_performance_monitor()
        
    @property
    def performance(self) -> PerformanceMonitor:
        """获取性能监控器（供外部查询）."""
        return self._monitor
    
    async def process_input(self, caller, text, session=None):
        """处理玩家输入（添加监控）."""
        with span("engine.process_input", tags={"caller": caller.key}):
            # ... 原有处理逻辑 ...
            result = await self._commands.handle(caller, text, session)
            
            # 记录命令统计
            if result and hasattr(result, 'success'):
                self._monitor.increment(
                    "command.total",
                    tags={"success": str(result.success)}
                )
            
            return result
    
    def get_performance_report(self) -> dict:
        """生成性能报告（用于开发者模式）."""
        stats = self._monitor.get_all_stats()
        
        # 添加引擎特定统计
        if self._objects:
            stats["engine"] = {
                "objects_cached": self._objects.get_cache_stats()["l1_cache_size"],
                "dirty_objects": self._objects.get_cache_stats()["dirty_objects"]
            }
        
        return stats
```

### 4.2 核心系统埋点

```python
# src/engine/commands/handler.py

from src.utils.performance_hooks import timed, counted

class CommandHandler:
    
    @counted("command.invoked")
    @timed("command.execution")
    async def handle(self, caller, raw_input, session=None):
        """处理命令（自动监控）."""
        # ... 原有逻辑 ...


# src/engine/objects/manager.py

from src.utils.performance_hooks import timed, span

class ObjectManager:
    
    @timed("db.query", tags={"type": "select"})
    async def _get_from_db(self, obj_id: int) -> ObjectModel | None:
        """从数据库获取对象（自动监控耗时）."""
        # ... 原有逻辑 ...
    
    @timed("db.query", tags={"type": "insert"})
    async def create(self, ...):
        # ... 原有逻辑 ...


# src/engine/database/connection.py

from src.utils.performance_hooks import timed

class DatabaseManager:
    
    @timed("db.execute")
    async def execute(self, sql: str, parameters: tuple = ()):
        """执行SQL（自动监控）."""
        # ... 原有逻辑 ...
```

### 4.3 游戏系统埋点

```python
# src/game/combat/core.py

from src.utils.performance_hooks import span, counted

class CombatSession:
    
    @counted("combat.started")
    async def start(self) -> None:
        """开始战斗."""
        with span("combat.session", tags={"participants": len(self.participants)}):
            # ... 原有逻辑 ...
    
    async def _combat_loop(self) -> None:
        """战斗主循环."""
        while self.active:
            with span("combat.tick"):
                # ... 原有逻辑 ...
                await asyncio.sleep(0.1)
```

---

## 5. 配置与部署

### 5.1 配置文件

```yaml
# config/performance.yaml

performance:
  # 是否启用监控
  enabled: true
  
  # 采样率（1.0 = 100%，0.1 = 10%）
  sampling_rate: 1.0
  
  # 慢操作阈值（毫秒）
  slow_threshold_ms: 100
  
  # 环形缓冲区大小
  max_metrics: 10000
  histogram_buckets: 1000
  
  # 各模块开关
  modules:
    command: true      # 命令系统
    database: true     # 数据库
    cache: true        # 缓存
    combat: true       # 战斗系统
    quest: false       # 任务系统（按需开启）
```

### 5.2 环境差异化配置

| 环境 | 采样率 | 缓冲区大小 | 慢查询阈值 | 用途 |
|:---|:---:|:---:|:---:|:---|
| 开发 | 1.0 | 10000 | 50ms | 详细调试 |
| 测试 | 0.5 | 5000 | 100ms | 集成测试 |
| 生产 | 0.1 | 1000 | 200ms | 轻量监控 |

---

## 6. 数据导出与展示

### 6.1 实时数据流（供GUI使用）

```python
# 引擎提供接口
class GameEngine:
    def subscribe_metrics(self, callback: Callable[[Metric], None]):
        """订阅实时指标（GUI面板使用）."""
        # 返回取消订阅函数
        pass
```

### 6.2 批量导出

```python
# 导出为JSON
report = engine.get_performance_report()
# {
#   "counters": {"command.total": 1500},
#   "gauges": {"memory.usage_mb": 256},
#   "histograms": {"db.query": {"avg": 12.5, "p95": 45.0}},
#   "engine": {"objects_cached": 150}
# }
```

### 6.3 GUI面板设计（阶段4使用）

```
┌─────────────────────────────────────────┐
│  性能监控面板                            │
├─────────────────────────────────────────┤
│  实时指标                                │
│  ├── 命令/秒: 15.2                       │
│  ├── 平均响应: 23ms                      │
│  ├── L1缓存命中率: 94%                   │
│  └── 活跃对象: 152                       │
│                                          │
│  图表（最近60秒）                         │
│  ┌─────────────────────────┐           │
│  │  响应时间趋势图          │           │
│  │  ═══════════════════    │           │
│  └─────────────────────────┘           │
│                                          │
│  慢查询告警（>100ms）                     │
│  ├── 14:32:15 db.query 245ms            │
│  └── 14:31:02 command.move 120ms        │
└─────────────────────────────────────────┘
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# tests/unit/test_performance_monitor.py

class TestPerformanceMonitor:
    """PerformanceMonitor 单元测试."""
    
    def test_record_counter(self):
        """测试计数器记录."""
        monitor = PerformanceMonitor()
        monitor.increment("test.counter")
        monitor.increment("test.counter")
        assert monitor.get_counter("test.counter") == 2
    
    def test_histogram_stats(self):
        """测试直方图统计计算."""
        monitor = PerformanceMonitor()
        for i in range(100):
            monitor.histogram("test.latency", float(i))
        
        stats = monitor.get_histogram("test.latency")
        assert stats.count == 100
        assert stats.min == 0
        assert stats.max == 99
        assert 49 <= stats.p50 <= 50
    
    def test_ring_buffer_overflow(self):
        """测试环形缓冲区溢出处理."""
        monitor = PerformanceMonitor(max_metrics=10)
        for i in range(20):
            monitor.gauge("test.gauge", float(i))
        
        # 只保留最近10个
        assert len(monitor._metrics) == 10
    
    def test_thread_safety(self):
        """测试线程安全."""
        import threading
        monitor = PerformanceMonitor()
        
        def worker():
            for _ in range(100):
                monitor.increment("thread.test")
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert monitor.get_counter("thread.test") == 1000


class TestPerformanceHooks:
    """装饰器和上下文管理器测试."""
    
    @pytest.mark.asyncio
    async def test_timed_decorator(self):
        """测试@timed装饰器."""
        @timed("test.function")
        async def slow_function():
            await asyncio.sleep(0.01)
            return 42
        
        result = await slow_function()
        assert result == 42
        
        stats = get_performance_monitor().get_histogram("test.function")
        assert stats is not None
        assert stats.count >= 1
    
    def test_span_context_manager(self):
        """测试span上下文管理器."""
        with span("test.operation"):
            time.sleep(0.01)
        
        stats = get_performance_monitor().get_histogram("test.operation")
        assert stats is not None
```

### 7.2 性能测试

```python
# tests/unit/test_performance_overhead.py

class TestPerformanceOverhead:
    """验证监控本身的开销."""
    
    def test_monitor_overhead(self):
        """测试监控开销 < 1%."""
        import timeit
        
        # 无监控
        def baseline():
            return sum(range(1000))
        
        # 有监控
        @timed("overhead.test")
        def with_monitor():
            return sum(range(1000))
        
        baseline_time = timeit.timeit(baseline, number=10000)
        monitored_time = timeit.timeit(with_monitor, number=10000)
        
        overhead = (monitored_time - baseline_time) / baseline_time
        assert overhead < 0.01  # < 1%
```

---

## 8. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|:---|:---:|:---:|:---|
| **内存泄漏** | 中 | 高 | 环形缓冲区固定大小，定期清理 |
| **性能开销超标** | 低 | 高 | 采样率控制，生产环境0.1 |
| **线程竞争** | 低 | 中 | 细粒度锁，批量操作 |
| **配置错误** | 中 | 低 | 配置验证，默认值安全 |
| **与现有代码冲突** | 低 | 中 | 装饰器方式，非侵入式 |

---

## 9. 实施计划

### 阶段 3.1: 基础设施 (2-3小时)
- [ ] 创建 `src/utils/performance.py`（核心实现）
- [ ] 创建 `src/utils/performance_hooks.py`（装饰器）
- [ ] 单元测试覆盖

### 阶段 3.2: 核心系统埋点 (3-4小时)
- [ ] `CommandHandler.handle()` 添加 `@timed`
- [ ] `ObjectManager` 数据库操作添加监控
- [ ] `DatabaseManager.execute()` 添加监控
- [ ] `GameEngine.process_input()` 添加 `span`

### 阶段 3.3: 游戏系统埋点 (可选，2-3小时)
- [ ] `CombatSession` 战斗监控
- [ ] 任务系统监控（按需）

### 阶段 3.4: 集成与导出 (2小时)
- [ ] 引擎集成 `engine.performance`
- [ ] 配置系统集成
- [ ] 文档完善

---

## 10. 验收标准

| 检查项 | 标准 | 验证方式 |
|:---|:---|:---|
| 功能完整 | 所有设计API可用 | 单元测试通过 |
| 性能达标 | 开销 < 1% | benchmark测试 |
| 线程安全 | 并发无异常 | 压力测试 |
| 文档完整 | API文档 + 使用指南 | 文档评审 |
| 集成成功 | GUI可查询数据 | 集成测试 |

---

## 附录A: 命名规范

```
# 指标命名规范
{模块}.{操作}.{属性}

示例:
command.execution.duration    # 命令执行耗时
db.query.count               # 数据库查询次数
cache.l1.hit_rate            # L1缓存命中率
combat.round.duration        # 战斗回合耗时
```

## 附录B: 相关文档

- 性能优化设计: `docs/performance_optimization_design.md`
- 性能优化实现: `docs/performance_optimizations.md`
- 开发者模式规划: `DEVELOPMENT_PLAN.md` 阶段6

---

**评审记录**

| 日期 | 评审人 | 意见 | 状态 |
|:---|:---|:---|:---:|
| 2026-02-26 | - | 初始版本 | 📝 待评审 |

---

*文档版本: 1.0 | 最后更新: 2026-02-26*

"""性能基准测试套件.

用于测量关键操作的性能指标.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar('T')


@dataclass
class BenchmarkResult:
    """基准测试结果."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    
    @property
    def ops_per_second(self) -> float:
        """每秒操作数."""
        return self.iterations / self.total_time if self.total_time > 0 else 0
    
    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  迭代次数: {self.iterations}\n"
            f"  总时间: {self.total_time:.4f}s\n"
            f"  平均: {self.avg_time*1000:.4f}ms\n"
            f"  最小: {self.min_time*1000:.4f}ms\n"
            f"  最大: {self.max_time*1000:.4f}ms\n"
            f"  QPS: {self.ops_per_second:.2f}"
        )


def benchmark(
    name: str,
    func: Callable[[], T],
    iterations: int = 100,
    warmup: int = 10,
) -> BenchmarkResult:
    """执行基准测试.
    
    Args:
        name: 测试名称
        func: 测试函数
        iterations: 迭代次数
        warmup: 预热次数
        
    Returns:
        测试结果
    """
    # 预热
    for _ in range(warmup):
        func()
    
    # 正式测试
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    
    total = sum(times)
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time=total,
        avg_time=total / iterations,
        min_time=min(times),
        max_time=max(times),
    )


async def async_benchmark(
    name: str,
    func: Callable[[], T],
    iterations: int = 100,
    warmup: int = 10,
) -> BenchmarkResult:
    """执行异步基准测试.
    
    Args:
        name: 测试名称
        func: 异步测试函数
        iterations: 迭代次数
        warmup: 预热次数
        
    Returns:
        测试结果
    """
    import asyncio
    
    # 预热
    for _ in range(warmup):
        await func()
    
    # 正式测试
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append(end - start)
    
    total = sum(times)
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time=total,
        avg_time=total / iterations,
        min_time=min(times),
        max_time=max(times),
    )

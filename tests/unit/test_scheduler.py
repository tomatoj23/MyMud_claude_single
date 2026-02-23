"""EventScheduler 单元测试 - 补充覆盖率.

测试scheduler.py中未被覆盖的代码路径。
"""

from __future__ import annotations

import asyncio
from unittest.mock import Mock, patch

import pytest

from src.engine.events.scheduler import EventScheduler, EventType


class TestEventSchedulerTimeScale:
    """时间膨胀系数测试."""

    def test_default_time_scale(self):
        """测试默认时间系数."""
        scheduler = EventScheduler()
        assert scheduler.time_scale == 1.0

    def test_set_time_scale(self):
        """测试设置时间系数."""
        scheduler = EventScheduler()
        scheduler.time_scale = 2.0
        assert scheduler._time_scale == 2.0

    def test_set_time_scale_invalid(self):
        """测试设置无效时间系数."""
        scheduler = EventScheduler()
        with pytest.raises(ValueError, match="时间系数必须大于0"):
            scheduler.time_scale = 0.0
        with pytest.raises(ValueError, match="时间系数必须大于0"):
            scheduler.time_scale = -1.0

    def test_set_time_scale_method(self):
        """测试set_time_scale方法."""
        scheduler = EventScheduler()
        scheduler.set_time_scale(0.5)
        assert scheduler.time_scale == 0.5


class TestEventSchedulerScheduleMethods:
    """事件安排方法测试."""

    def test_schedule_delay(self):
        """测试安排延迟事件."""
        scheduler = EventScheduler()
        callback = Mock()
        
        event_id = scheduler.schedule_delay(callback, delay=1.0, priority=5)
        
        assert event_id is not None
        assert len(scheduler._queue) == 1

    def test_schedule_interval(self):
        """测试安排周期事件."""
        scheduler = EventScheduler()
        callback = Mock()
        
        event_id = scheduler.schedule_interval(
            callback, interval=2.0, repeat=5, priority=3
        )
        
        assert event_id is not None
        assert len(scheduler._queue) == 1

    def test_schedule_condition(self):
        """测试安排条件事件."""
        scheduler = EventScheduler()
        callback = Mock()
        condition = lambda: True
        
        event_id = scheduler.schedule_condition(
            callback, condition, check_interval=1.0, priority=0
        )
        
        assert event_id is not None
        assert len(scheduler._queue) == 1

    def test_schedule_frame(self):
        """测试安排帧事件."""
        scheduler = EventScheduler()
        callback = Mock()
        
        event_id = scheduler.schedule_frame(callback, priority=1)
        
        assert event_id is not None
        assert len(scheduler._frame_events) == 1

    def test_schedule_frame_event_priority(self):
        """测试帧事件优先级排序."""
        scheduler = EventScheduler()
        
        # 添加多个不同优先级的帧事件
        id1 = scheduler.schedule_frame(Mock(), priority=5)
        id2 = scheduler.schedule_frame(Mock(), priority=1)
        id3 = scheduler.schedule_frame(Mock(), priority=3)
        
        assert len(scheduler._frame_events) == 3


class TestEventSchedulerCancel:
    """事件取消测试."""

    def test_cancel_existing_event(self):
        """测试取消存在的队列事件."""
        scheduler = EventScheduler()
        callback = Mock()
        
        event_id = scheduler.schedule_delay(callback, delay=1.0)
        result = scheduler.cancel(event_id)
        
        assert result is True
        assert event_id in scheduler._cancelled_events

    def test_cancel_existing_frame_event(self):
        """测试取消存在的帧事件."""
        scheduler = EventScheduler()
        callback = Mock()
        
        event_id = scheduler.schedule_frame(callback)
        result = scheduler.cancel(event_id)
        
        assert result is True
        assert len(scheduler._frame_events) == 0

    def test_cancel_nonexistent_event(self):
        """测试取消不存在的事件."""
        scheduler = EventScheduler()
        
        result = scheduler.cancel("nonexistent-id")
        
        assert result is False


class TestEventSchedulerLifecycle:
    """调度器生命周期测试."""

    def test_start_when_running(self):
        """测试运行时重复启动."""
        scheduler = EventScheduler()
        scheduler._running = True
        
        # 不应该抛出异常
        scheduler.start()

    def test_stop_when_not_running(self):
        """测试停止未运行的调度器."""
        scheduler = EventScheduler()
        
        # 不应该抛出异常
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_run_cancelled(self):
        """测试运行被取消."""
        scheduler = EventScheduler()
        scheduler._running = True
        
        task = asyncio.create_task(scheduler.run())
        await asyncio.sleep(0.01)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_run_exception(self):
        """测试运行中异常."""
        scheduler = EventScheduler()
        
        # 添加一个会抛出异常的事件
        async def bad_callback():
            raise Exception("Test error")
        
        scheduler.schedule_delay(bad_callback, delay=0.001)
        
        scheduler.start()
        await asyncio.sleep(0.02)
        scheduler.stop()


class TestEventSchedulerExecute:
    """事件执行测试."""

    @pytest.mark.asyncio
    async def test_execute_condition_event_true(self):
        """测试条件事件（条件为真）."""
        scheduler = EventScheduler()
        callback = Mock()
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.CONDITION,
            callback=callback,
            delay=0.1,
            condition=lambda: True,
        )
        
        await scheduler._execute_event(event)
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_condition_event_false(self):
        """测试条件事件（条件为假）."""
        scheduler = EventScheduler()
        callback = Mock()
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.CONDITION,
            callback=callback,
            delay=0.1,
            condition=lambda: False,
        )
        
        await scheduler._execute_event(event)
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_interval_event_repeat(self):
        """测试周期事件重复安排."""
        scheduler = EventScheduler()
        
        async def callback():
            pass
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.INTERVAL,
            callback=callback,
            delay=0.1,
            repeat=2,
        )
        
        await scheduler._execute_event(event)
        # 应该重新安排事件
        assert len(scheduler._queue) == 1

    @pytest.mark.asyncio
    async def test_execute_interval_event_no_repeat(self):
        """测试周期事件不重复."""
        scheduler = EventScheduler()
        
        async def callback():
            pass
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.INTERVAL,
            callback=callback,
            delay=0.1,
            repeat=1,
        )
        
        await scheduler._execute_event(event)
        # 不应该重新安排
        assert len(scheduler._queue) == 0

    @pytest.mark.asyncio
    async def test_execute_event_exception(self):
        """测试事件执行异常处理."""
        scheduler = EventScheduler()
        
        async def bad_callback():
            raise Exception("Test error")
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.DELAY,
            callback=bad_callback,
            delay=0.1,
        )
        
        # 不应该抛出异常
        await scheduler._execute_event(event)

    @pytest.mark.asyncio
    async def test_execute_frame_event(self):
        """测试帧事件执行."""
        scheduler = EventScheduler()
        callback = Mock()
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.FRAME,
            callback=callback,
        )
        
        await scheduler._execute_frame_event(event)
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_frame_event_exception(self):
        """测试帧事件执行异常."""
        scheduler = EventScheduler()
        
        async def bad_callback():
            raise Exception("Test error")
        
        from src.engine.events.scheduler import Event
        event = Event(
            id="test",
            event_type=EventType.FRAME,
            callback=bad_callback,
        )
        
        # 不应该抛出异常
        await scheduler._execute_frame_event(event)


class TestEventSchedulerRunLoop:
    """运行循环测试."""

    @pytest.mark.asyncio
    async def test_run_with_cancelled_event(self):
        """测试运行循环处理已取消事件."""
        scheduler = EventScheduler()
        scheduler._running = True
        
        async def callback():
            pass
        
        event_id = scheduler.schedule_delay(callback, delay=0.001)
        scheduler._cancelled_events.add(event_id)
        
        # 启动并在短时间后停止
        task = asyncio.create_task(scheduler.run())
        await asyncio.sleep(0.02)
        scheduler.stop()
        
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_run_with_frame_event_cancelled(self):
        """测试运行循环处理已取消的帧事件."""
        scheduler = EventScheduler()
        scheduler._running = True
        
        async def callback():
            pass
        
        event_id = scheduler.schedule_frame(callback)
        scheduler._cancelled_events.add(event_id)
        
        task = asyncio.create_task(scheduler.run())
        await asyncio.sleep(0.02)
        scheduler.stop()
        
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestEventSchedulerStats:
    """统计信息测试."""

    def test_get_stats(self):
        """测试获取统计信息."""
        scheduler = EventScheduler()
        
        # 添加一些事件
        scheduler.schedule_delay(Mock(), delay=1.0)
        scheduler.schedule_frame(Mock())
        
        stats = scheduler.get_stats()
        
        assert stats["queue_size"] == 1
        assert stats["frame_events"] == 1
        assert stats["time_scale"] == 1.0
        assert stats["running"] is False

    def test_is_running(self):
        """测试运行状态检查."""
        scheduler = EventScheduler()
        assert scheduler.is_running() is False
        
        scheduler._running = True
        assert scheduler.is_running() is True


class TestEventLessThan:
    """Event比较测试."""

    def test_event_less_than(self):
        """测试事件优先级比较."""
        from src.engine.events.scheduler import Event, EventType
        
        event1 = Event(
            id="1",
            event_type=EventType.DELAY,
            callback=Mock(),
            priority=1,
        )
        event2 = Event(
            id="2",
            event_type=EventType.DELAY,
            callback=Mock(),
            priority=5,
        )
        
        assert event1 < event2

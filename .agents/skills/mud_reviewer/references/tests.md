# 测试模板

## 单元测试模板

### AttributeHandler测试

```python
# tests/unit/test_typeclass.py
import pytest
from src.engine.core.typeclass import TypeclassBase, AttributeHandler


class TestAttributeHandler:
    """AttributeHandler测试套件"""
    
    @pytest.fixture
    def mock_obj(self):
        """创建模拟对象"""
        class MockObj:
            _db_model = type('DBModel', (), {'attributes': {}})()
            def mark_dirty(self): pass
        return MockObj()
    
    def test_getattr_existing(self, mock_obj):
        """测试获取已存在属性"""
        mock_obj._db_model.attributes = {"strength": 10}
        handler = AttributeHandler(mock_obj)
        
        assert handler.strength == 10
    
    def test_getattr_nonexistent(self, mock_obj):
        """测试获取不存在属性返回None"""
        handler = AttributeHandler(mock_obj)
        
        assert handler.nonexistent is None
    
    def test_setattr_marks_dirty(self, mock_obj):
        """测试设置属性标记脏数据"""
        dirty_called = [False]
        def mark_dirty():
            dirty_called[0] = True
        mock_obj.mark_dirty = mark_dirty
        
        handler = AttributeHandler(mock_obj)
        handler.strength = 15
        
        assert dirty_called[0]
        assert handler.strength == 15
    
    def test_cache_consistency(self, mock_obj):
        """测试缓存一致性"""
        mock_obj._db_model.attributes = {"value": 1}
        handler = AttributeHandler(mock_obj)
        
        # 第一次获取，写入缓存
        assert handler.value == 1
        
        # 修改缓存
        handler.value = 2
        assert handler.value == 2
```

### Command测试

```python
# tests/unit/test_commands.py
import pytest
from src.engine.commands.base import Command
from src.engine.commands.cmdset import CmdSet


class MockCommand(Command):
    """测试用命令"""
    key = "mock"
    aliases = ["m"]
    
    def execute(self):
        self.caller.last_cmd = self.cmd_string


class TestCommand:
    """Command基类测试"""
    
    @pytest.fixture
    def mock_caller(self):
        class MockCaller:
            last_cmd = None
        return MockCaller()
    
    def test_command_execution(self, mock_caller):
        """测试命令执行"""
        cmd = MockCommand(mock_caller, "mock", "arg")
        cmd.execute()
        
        assert mock_caller.last_cmd == "mock"
    
    def test_check_access_default(self, mock_caller):
        """测试默认权限通过"""
        cmd = MockCommand(mock_caller, "mock", "")
        
        assert cmd.check_access() is True


class TestCmdSet:
    """CmdSet测试"""
    
    def test_add_command(self):
        """测试添加命令"""
        cmdset = CmdSet()
        cmdset.add(MockCommand)
        
        assert "mock" in cmdset.commands
        assert "m" in cmdset.commands
    
    def test_merge_priority(self):
        """测试合并优先级"""
        high_priority = CmdSet()
        high_priority.priority = 10
        high_priority.add(MockCommand)
        
        low_priority = CmdSet()
        low_priority.priority = 5
        
        merged = high_priority.merge(low_priority)
        
        assert merged.commands["mock"] == MockCommand
```

## 集成测试模板

### 事件调度集成测试

```python
# tests/integration/test_scheduler.py
import pytest
import asyncio
from src.engine.core.scheduler import EventScheduler, Event, EventType


class TestEventScheduler:
    """EventScheduler集成测试"""
    
    @pytest.fixture
    async def scheduler(self):
        """创建并启动调度器"""
        s = EventScheduler()
        task = asyncio.create_task(s.run())
        yield s
        s.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_delay_event(self, scheduler):
        """测试延迟事件"""
        called = [False]
        
        async def callback():
            called[0] = True
        
        event = Event(
            id="test_delay",
            event_type=EventType.DELAY,
            callback=callback,
            delay=0.1
        )
        scheduler.schedule(event)
        
        await asyncio.sleep(0.2)
        
        assert called[0]
    
    @pytest.mark.asyncio
    async def test_interval_event(self, scheduler):
        """测试周期事件"""
        call_count = [0]
        
        async def callback():
            call_count[0] += 1
        
        event = Event(
            id="test_interval",
            event_type=EventType.INTERVAL,
            callback=callback,
            delay=0.1,
            repeat=3
        )
        scheduler.schedule(event)
        
        await asyncio.sleep(0.4)
        
        assert call_count[0] == 3
    
    @pytest.mark.asyncio
    async def test_time_scale(self, scheduler):
        """测试时间膨胀"""
        scheduler.set_time_scale(2.0)  # 2倍速
        
        called_at = [0.0]
        
        async def callback():
            called_at[0] = asyncio.get_event_loop().time()
        
        event = Event(
            id="test_scale",
            event_type=EventType.DELAY,
            callback=callback,
            delay=0.2  # 实际应该0.1秒后执行
        )
        
        start = asyncio.get_event_loop().time()
        scheduler.schedule(event)
        
        await asyncio.sleep(0.15)
        
        # 0.15秒实际时间，2倍速 = 0.3秒游戏时间
        assert called_at[0] > 0
```

## 测试运行检查清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 异步测试使用 `pytest-asyncio`
- [ ] 数据库测试使用事务回滚
- [ ] Mock对象不依赖外部资源

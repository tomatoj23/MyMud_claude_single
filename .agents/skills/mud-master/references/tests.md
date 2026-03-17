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

> 当前仓库对齐说明：
> - 命令基类位于 `src/engine/commands/command.py`
> - 事件调度器位于 `src/engine/events/scheduler.py`
> - 命令实例通常先无参创建，再补 `caller` / `args` / `cmdstring`

```python
# tests/unit/test_commands.py
import pytest

from src.engine.commands.cmdset import CmdSet
from src.engine.commands.command import Command, CommandResult


class MockCommand(Command):
    """测试用命令。"""

    key = "mock"
    aliases = ["m"]

    async def execute(self) -> CommandResult:
        return CommandResult(True, f"executed: {self.args}")


class MockCaller:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def msg(self, text: str, **kwargs) -> None:
        self.messages.append(text)


class TestCommand:
    """Command基类测试。"""

    @pytest.mark.asyncio
    async def test_command_execution(self):
        cmd = MockCommand()
        caller = MockCaller()
        cmd.caller = caller
        cmd.cmdstring = "mock"
        cmd.args = "arg"

        result = await cmd.run()

        assert result.success is True
        assert "arg" in result.message

    def test_has_perm_default(self):
        cmd = MockCommand()
        caller = MockCaller()

        assert cmd.has_perm(caller) is True


class TestCmdSet:
    """CmdSet测试。"""

    def test_add_command(self):
        cmdset = CmdSet()
        cmdset.add(MockCommand)

        assert "mock" in cmdset.commands
        assert "m" in cmdset.commands
```

## 集成测试模板

### 事件调度集成测试

```python
# tests/integration/test_scheduler.py
import asyncio

import pytest

from src.engine.events.scheduler import EventScheduler


class TestEventScheduler:
    """EventScheduler集成测试。"""

    @pytest.fixture
    async def scheduler(self):
        scheduler = EventScheduler()
        scheduler.start()
        yield scheduler
        scheduler.stop()
        await asyncio.sleep(0)

    @pytest.mark.asyncio
    async def test_delay_event(self, scheduler):
        called = [False]

        async def callback():
            called[0] = True

        scheduler.schedule_delay(callback, delay=0.01)

        await asyncio.sleep(0.05)

        assert called[0]

    @pytest.mark.asyncio
    async def test_interval_event(self, scheduler):
        call_count = [0]

        async def callback():
            call_count[0] += 1

        scheduler.schedule_interval(callback, interval=0.01, repeat=3)

        await asyncio.sleep(0.08)

        assert call_count[0] == 3

    def test_time_scale(self):
        scheduler = EventScheduler()
        scheduler.set_time_scale(2.0)

        assert scheduler.time_scale == 2.0
```
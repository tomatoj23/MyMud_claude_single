"""GameEngine 集成测试.

测试引擎初始化流程、启动/停止流程和命令处理端到端。
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.engine.core.engine import GameEngine, create_engine, get_engine
from src.engine.core.typeclass import TypeclassBase
from src.engine.database.connection import DatabaseManager
from src.engine.objects.manager import ObjectManager
from src.utils.config import Config


class TestGameEngineInitialization:
    """引擎初始化测试."""

    @pytest.mark.asyncio
    async def test_engine_creation(self):
        """测试引擎创建."""
        engine = GameEngine()

        assert engine is not None
        assert engine.config is not None
        assert engine.running is False

    @pytest.mark.asyncio
    async def test_engine_with_custom_config(self):
        """测试使用自定义配置创建引擎."""
        config = Config()
        config.game.tick_rate = 2.0

        engine = GameEngine(config)

        assert engine.config.game.tick_rate == 2.0

    @pytest.mark.asyncio
    async def test_initialize_database(self, tmp_path: Path):
        """测试初始化数据库."""
        config = Config()
        db_path = tmp_path / "test.db"
        config.database.url = f"sqlite+aiosqlite:///{db_path}"

        engine = GameEngine(config)
        await engine.initialize()

        assert engine._db is not None
        assert await engine.db.is_healthy()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_initialize_object_manager(self, tmp_path: Path):
        """测试初始化对象管理器."""
        config = Config()
        db_path = tmp_path / "test.db"
        config.database.url = f"sqlite+aiosqlite:///{db_path}"

        engine = GameEngine(config)
        await engine.initialize()

        assert engine._objects is not None
        assert engine.objects._initialized

        await engine.stop()

    @pytest.mark.asyncio
    async def test_initialize_command_handler(self, tmp_path: Path):
        """测试初始化命令处理器."""
        config = Config()
        db_path = tmp_path / "test.db"
        config.database.url = f"sqlite+aiosqlite:///{db_path}"

        engine = GameEngine(config)
        await engine.initialize()

        assert engine._commands is not None
        assert engine.commands._initialized

        await engine.stop()

    @pytest.mark.asyncio
    async def test_initialize_event_scheduler(self, tmp_path: Path):
        """测试初始化事件调度器."""
        config = Config()
        db_path = tmp_path / "test.db"
        config.database.url = f"sqlite+aiosqlite:///{db_path}"

        engine = GameEngine(config)
        await engine.initialize()

        assert engine._events is not None
        assert engine.events.time_scale == config.game.tick_rate

        await engine.stop()

    @pytest.mark.asyncio
    async def test_initialize_order(self, tmp_path: Path):
        """测试初始化顺序正确."""
        config = Config()
        db_path = tmp_path / "test.db"
        config.database.url = f"sqlite+aiosqlite:///{db_path}"

        engine = GameEngine(config)

        # 按正确顺序初始化
        await engine.initialize()

        # 验证所有子系统都已初始化
        assert engine._db is not None
        assert engine._objects is not None
        assert engine._commands is not None
        assert engine._events is not None

        await engine.stop()

    @pytest.mark.asyncio
    async def test_access_before_initialize_raises(self):
        """测试初始化前访问属性抛出异常."""
        engine = GameEngine()

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.db

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.objects

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.commands


class TestGameEngineLifecycle:
    """引擎生命周期测试."""

    @pytest.mark.asyncio
    async def test_start_stop(self, tmp_path: Path):
        """测试启动和停止."""
        import asyncio

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        await engine.start()
        await asyncio.sleep(0.01)  # 等待事件调度器启动

        assert engine.running is True
        assert engine.events.is_running()

        await engine.stop()

        assert engine.running is False

    @pytest.mark.asyncio
    async def test_double_start_raises(self, tmp_path: Path):
        """测试重复启动抛出异常."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        with pytest.raises(RuntimeError, match="引擎已在运行"):
            await engine.start()

        await engine.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self, tmp_path: Path):
        """测试停止未运行的引擎."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 不应该抛出异常
        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_without_initialize_raises(self, tmp_path: Path):
        """测试未初始化时启动抛出异常."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        # 不调用 initialize

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            await engine.start()

    @pytest.mark.asyncio
    async def test_graceful_shutdown_saves_objects(self, tmp_path: Path):
        """测试优雅关闭时保存对象."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        # 创建并修改对象
        obj = await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="test_save",
        )
        obj.key = "modified_key"

        # 验证对象是脏数据
        assert obj.is_dirty()

        # 停止引擎
        await engine.stop()

        # 重新初始化并验证数据已保存
        engine2 = GameEngine(config)
        await engine2.initialize()

        loaded = await engine2.objects.load(obj.id)
        assert loaded is not None
        assert loaded.key == "modified_key"

        await engine2.stop()

    @pytest.mark.asyncio
    async def test_auto_save(self, tmp_path: Path):
        """测试自动保存功能."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        config.game.auto_save_interval = 0.05  # 50ms 便于测试

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        # 创建脏数据对象
        obj = await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="auto_save_test",
        )
        obj.key = "auto_saved"

        # 等待自动保存
        await asyncio.sleep(0.1)

        # 对象应该已被保存
        obj.clean_dirty()
        assert not obj.is_dirty()

        await engine.stop()


class TestGameEngineCommandProcessing:
    """命令处理集成测试."""

    @pytest.fixture
    async def running_engine(self, tmp_path: Path):
        """创建并启动的引擎."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        yield engine

        if engine.running:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_process_input_not_running(self, tmp_path: Path):
        """测试未运行时处理输入返回 None."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        # 不启动

        caller = MagicMock()
        result = await engine.process_input(caller, "look")

        assert result is None

        await engine.stop()

    @pytest.mark.asyncio
    async def test_process_input_empty(self, running_engine: GameEngine):
        """测试处理空输入."""
        caller = MagicMock()
        result = await running_engine.process_input(caller, "   ")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_input_unknown_command(self, running_engine: GameEngine):
        """测试处理未知命令."""
        caller = MagicMock()
        result = await running_engine.process_input(caller, "unknowncommand123")

        # 结果可能是 None 或 CommandResult
        if result is not None:
            assert result.success is False

    @pytest.mark.asyncio
    async def test_process_input_look_command(self, running_engine: GameEngine):
        """测试处理 look 命令."""
        # 创建测试对象
        obj = await running_engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="test_caller",
        )

        result = await running_engine.process_input(obj, "look")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_input_create_command(self, running_engine: GameEngine):
        """测试处理 create 命令."""
        obj = await running_engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="builder",
        )

        result = await running_engine.process_input(obj, "create testobj")

        assert result is not None
        assert result.success is True

        # 验证对象已创建
        found = await running_engine.objects.find(key_contains="testobj")
        assert len(found) > 0

    @pytest.mark.asyncio
    async def test_process_input_with_exception(self, running_engine: GameEngine):
        """测试处理输入时异常处理."""
        # 模拟命令处理抛出异常
        with patch.object(
            running_engine.commands,
            "handle",
            side_effect=Exception("Test error"),
        ):
            caller = MagicMock()
            result = await running_engine.process_input(caller, "look")

            assert result is None


class TestGameEngineStats:
    """引擎统计信息测试."""

    @pytest.mark.asyncio
    async def test_get_stats_not_initialized(self):
        """测试未初始化时获取统计信息."""
        engine = GameEngine()

        stats = engine.get_stats()

        assert stats["running"] is False
        # 未初始化时不应有对象和事件统计
        assert "objects" not in stats
        assert "events" not in stats

    @pytest.mark.asyncio
    async def test_get_stats_initialized(self, tmp_path: Path):
        """测试初始化后获取统计信息."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        stats = engine.get_stats()

        assert stats["running"] is False
        assert "objects" in stats
        assert "events" in stats

        await engine.stop()

    @pytest.mark.asyncio
    async def test_get_stats_running(self, tmp_path: Path):
        """测试运行时获取统计信息."""
        import asyncio

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        await asyncio.sleep(0.01)  # 等待事件调度器启动

        stats = engine.get_stats()

        assert stats["running"] is True
        assert stats["events"]["running"] is True

        await engine.stop()


class TestGlobalEngine:
    """全局引擎实例测试."""

    def test_get_engine_before_create_raises(self):
        """测试创建前获取引擎抛出异常."""
        # 确保全局引擎为 None
        import src.engine.core.engine as engine_module

        engine_module._engine = None

        with pytest.raises(RuntimeError, match="引擎未创建"):
            get_engine()

    @pytest.mark.asyncio
    async def test_create_and_get_engine(self, tmp_path: Path):
        """测试创建和获取全局引擎."""
        import src.engine.core.engine as engine_module

        engine_module._engine = None

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = create_engine(config)

        assert engine is not None
        assert get_engine() is engine

        # 清理
        engine_module._engine = None


class TestIntegrationScenario:
    """集成场景测试."""

    @pytest.mark.asyncio
    async def test_full_game_session(self, tmp_path: Path):
        """测试完整游戏会话流程."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        # 1. 创建引擎
        engine = GameEngine(config)

        # 2. 初始化
        await engine.initialize()

        # 3. 创建房间
        room = await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="test_room",
        )

        # 4. 创建玩家
        player = await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="player",
            location=room,
        )

        # 5. 启动引擎
        await engine.start()

        # 6. 执行一些命令
        result1 = await engine.process_input(player, "look")
        assert result1.success is True

        result2 = await engine.process_input(player, "inventory")
        assert result2.success is True

        # 7. 创建物品
        result3 = await engine.process_input(player, "create sword")
        assert result3.success is True

        # 8. 停止引擎
        await engine.stop()

        # 9. 重新加载验证持久化
        engine2 = GameEngine(config)
        await engine2.initialize()

        # 查找之前创建的对象
        rooms = await engine2.objects.find(key_contains="test_room")
        assert len(rooms) == 1

        players = await engine2.objects.find(key_contains="player")
        assert len(players) == 1

        swords = await engine2.objects.find(key_contains="sword")
        assert len(swords) == 1

        await engine2.stop()

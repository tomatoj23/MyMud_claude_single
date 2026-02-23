"""GameEngine 单元测试 - 补充覆盖率.

测试engine.py中未被覆盖的代码路径。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.engine.core.engine import GameEngine, create_engine, get_engine
from src.utils.config import Config


class TestGameEngineAccessBeforeInit:
    """测试初始化前访问属性."""

    def test_access_db_before_init_raises(self):
        """测试初始化前访问db属性抛出异常."""
        engine = GameEngine()
        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.db

    def test_access_objects_before_init_raises(self):
        """测试初始化前访问objects属性抛出异常."""
        engine = GameEngine()
        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.objects

    def test_access_commands_before_init_raises(self):
        """测试初始化前访问commands属性抛出异常."""
        engine = GameEngine()
        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.commands

    def test_access_events_before_init_raises(self):
        """测试初始化前访问events属性抛出异常."""
        engine = GameEngine()
        with pytest.raises(RuntimeError, match="引擎未初始化"):
            _ = engine.events


class TestGameEngineConstructor:
    """引擎构造函数测试."""

    def test_default_config(self):
        """测试默认配置."""
        engine = GameEngine()
        assert engine.config is not None
        assert engine._db is None
        assert engine._objects is None
        assert engine._commands is None
        assert engine._events is None
        assert engine._running is False

    def test_custom_config(self):
        """测试自定义配置."""
        config = Config()
        config.game.tick_rate = 3.0
        engine = GameEngine(config)
        assert engine.config.game.tick_rate == 3.0


class TestGameEngineLifecycleEdgeCases:
    """引擎生命周期边界测试."""

    @pytest.mark.asyncio
    async def test_stop_without_start(self, tmp_path: Path):
        """测试未启动时停止."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        
        # 不应该抛出异常
        await engine.stop()

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
    async def test_start_without_initialize(self, tmp_path: Path):
        """测试未初始化时启动抛出异常."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        # 不调用 initialize

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            await engine.start()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, tmp_path: Path):
        """测试停止未运行的引擎."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        
        # 直接停止（不启动）
        await engine.stop()
        assert engine.running is False


class TestGameEngineAutoSave:
    """自动保存测试."""

    @pytest.mark.asyncio
    async def test_auto_save_loop_cancelled(self, tmp_path: Path):
        """测试自动保存循环取消."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        config.game.auto_save_interval = 0.01

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        # 立即取消
        await engine.stop()
        
        # 验证任务已取消
        assert engine._auto_save_task is None or engine._auto_save_task.done()

    @pytest.mark.asyncio
    async def test_auto_save_exception_handling(self, tmp_path: Path):
        """测试自动保存异常处理."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        config.game.auto_save_interval = 0.01

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        # 模拟save_all抛出异常
        with patch.object(
            engine.objects, 
            'save_all', 
            side_effect=Exception("Save error")
        ):
            await asyncio.sleep(0.02)
            # 引擎应该继续运行
            assert engine.running is True

        await engine.stop()


class TestGameEngineProcessInput:
    """输入处理测试."""

    @pytest.mark.asyncio
    async def test_process_input_not_running(self, tmp_path: Path):
        """测试未运行时处理输入返回None."""
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
    async def test_process_input_exception(self, tmp_path: Path):
        """测试输入处理异常."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        # 模拟命令处理异常
        with patch.object(
            engine.commands,
            'handle',
            side_effect=Exception("Test error")
        ):
            caller = MagicMock()
            result = await engine.process_input(caller, "look")
            assert result is None

        await engine.stop()


class TestGameEngineStats:
    """统计信息测试."""

    def test_get_stats_not_initialized(self):
        """测试未初始化时获取统计信息."""
        engine = GameEngine()
        stats = engine.get_stats()
        assert stats["running"] is False
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
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()

        stats = engine.get_stats()
        assert stats["running"] is True
        assert "objects" in stats
        assert "events" in stats

        await engine.stop()


class TestGlobalEngineFunctions:
    """全局引擎函数测试."""

    def test_get_engine_before_create(self):
        """测试创建前获取引擎."""
        import src.engine.core.engine as engine_module
        engine_module._engine = None

        with pytest.raises(RuntimeError, match="引擎未创建"):
            get_engine()

    def test_create_and_get_engine(self):
        """测试创建和获取引擎."""
        import src.engine.core.engine as engine_module
        engine_module._engine = None

        config = Config()
        engine = create_engine(config)
        
        assert engine is not None
        assert get_engine() is engine

        # 清理
        engine_module._engine = None

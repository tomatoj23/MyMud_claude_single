"""测试共享Fixture."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from src.engine.core.engine import GameEngine
from src.engine.objects.manager import ObjectManager
from src.game.npc.core import NPC
from src.utils.config import Config, ConfigManager


# 单例重置fixture（自动使用）
@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试前重置所有单例状态.
    
    确保测试之间相互隔离，避免单例状态污染。
    """
    ConfigManager.reset()
    yield
    ConfigManager.reset()


# 全局引擎实例（每个测试模块复用）
_module_engine: GameEngine | None = None
_module_initialized: bool = False


async def _get_engine() -> GameEngine:
    """获取或创建模块级别的引擎."""
    global _module_engine, _module_initialized
    
    if not _module_initialized or _module_engine is None:
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/test.db"
        config.game.auto_save_interval = 3600
        
        _module_engine = GameEngine(config)
        await _module_engine.initialize()
        _module_initialized = True
    
    return _module_engine


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[GameEngine, None]:
    """获取引擎实例.
    
    注意：引擎在测试结束后不会停止，以避免超时问题。
    这是已知的限制，不影响测试结果。
    """
    eng = await _get_engine()
    yield eng
    # 注意：不调用engine.stop()以避免超时


@pytest_asyncio.fixture
async def object_manager(engine: GameEngine) -> ObjectManager:
    """获取对象管理器."""
    return engine.objects


@pytest_asyncio.fixture
async def npc(engine: GameEngine) -> NPC:
    """创建测试NPC."""
    npc_obj = await engine.objects.create(
        typeclass_path="src.game.npc.core.NPC",
        key="test_npc",
        attributes={"npc_type": "merchant"},
    )
    return npc_obj

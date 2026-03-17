"""存档系统测试."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.engine.save import SaveInfo, SaveManager


class TestSaveInfo:
    """存档信息测试."""

    def test_create_save_info(self):
        """测试创建存档信息."""
        info = SaveInfo(
            slot="test",
            name="测试存档",
            timestamp="2026-03-17T10:00:00",
            version=1,
            play_time=3600,
            level=10,
            location="客栈",
            checksum="abc123",
            compressed_size=1024,
        )

        assert info.slot == "test"
        assert info.name == "测试存档"
        assert info.level == 10


class TestSaveManagerBasic:
    """存档管理器基础测试."""

    def test_save_dir_constant(self):
        """测试存档目录常量."""
        assert SaveManager.SAVE_DIR == Path("saves")
        assert SaveManager.SAVE_VERSION == 1

    def test_list_saves_empty(self):
        """测试列出空存档列表."""
        # 创建临时管理器（不需要真实引擎）
        class MockEngine:
            pass

        manager = SaveManager(MockEngine())  # type: ignore
        saves = manager.list_saves()
        assert isinstance(saves, list)

    def test_get_nonexistent_save_info(self):
        """测试获取不存在的存档信息."""
        class MockEngine:
            pass

        manager = SaveManager(MockEngine())  # type: ignore
        info = manager.get_save_info("nonexistent_slot")
        assert info is None

    def test_delete_nonexistent_save(self):
        """测试删除不存在的存档."""
        class MockEngine:
            pass

        manager = SaveManager(MockEngine())  # type: ignore
        # 不应抛出异常
        manager.delete_save("nonexistent_slot")

"""主题系统测试."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.themes import ThemeManager

# 设置无头模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def app():
    """创建Qt应用."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestThemeManager:
    """主题管理器测试."""

    def test_create_manager(self):
        """测试创建主题管理器."""
        manager = ThemeManager()
        assert manager is not None
        assert manager.current_theme == "dark"

    def test_apply_dark_theme(self, app):
        """测试应用暗色主题."""
        manager = ThemeManager()
        manager.apply_theme(app, "dark")
        assert manager.current_theme == "dark"
        assert app.styleSheet() != ""

    def test_apply_light_theme(self, app):
        """测试应用亮色主题."""
        manager = ThemeManager()
        manager.apply_theme(app, "light")
        assert manager.current_theme == "light"
        assert app.styleSheet() != ""

    def test_apply_nonexistent_theme(self, app):
        """测试应用不存在的主题."""
        manager = ThemeManager()
        original_theme = manager.current_theme
        manager.apply_theme(app, "nonexistent")
        # 主题不存在时不应改变当前主题
        assert manager.current_theme == original_theme

    def test_theme_files_exist(self):
        """测试主题文件存在."""
        themes_dir = Path(__file__).parent.parent.parent / "src" / "gui" / "themes"
        assert (themes_dir / "dark.qss").exists()
        assert (themes_dir / "light.qss").exists()

    def test_theme_files_not_empty(self):
        """测试主题文件不为空."""
        themes_dir = Path(__file__).parent.parent.parent / "src" / "gui" / "themes"

        dark_qss = themes_dir / "dark.qss"
        assert dark_qss.stat().st_size > 0

        light_qss = themes_dir / "light.qss"
        assert light_qss.stat().st_size > 0

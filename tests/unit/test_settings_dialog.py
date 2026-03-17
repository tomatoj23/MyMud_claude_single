"""设置对话框测试."""

from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.dialogs import SettingsDialog

# 设置无头模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def app():
    """创建Qt应用."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def dialog(app):
    """创建设置对话框."""
    dialog = SettingsDialog(app)
    yield dialog
    dialog.close()


class TestSettingsDialog:
    """设置对话框测试."""

    def test_create_dialog(self, dialog):
        """测试创建对话框."""
        assert dialog is not None
        assert dialog.windowTitle() == "设置"

    def test_tabs_exist(self, dialog):
        """测试标签页存在."""
        assert dialog._tab_widget.count() == 3
        assert dialog._tab_widget.tabText(0) == "外观"
        assert dialog._tab_widget.tabText(1) == "编辑器"
        assert dialog._tab_widget.tabText(2) == "游戏"

    def test_appearance_widgets(self, dialog):
        """测试外观设置控件."""
        assert dialog._theme_combo is not None
        assert dialog._font_family is not None
        assert dialog._font_size is not None
        assert dialog._window_width is not None
        assert dialog._window_height is not None

    def test_editor_widgets(self, dialog):
        """测试编辑器设置控件."""
        assert dialog._auto_complete is not None
        assert dialog._command_history is not None
        assert dialog._history_size is not None
        assert dialog._max_lines is not None
        assert dialog._timestamp is not None

    def test_game_widgets(self, dialog):
        """测试游戏设置控件."""
        assert dialog._auto_save is not None
        assert dialog._auto_save_interval is not None
        assert dialog._sound_enabled is not None
        assert dialog._confirm_quit is not None

    def test_default_values(self, dialog):
        """测试默认值."""
        assert dialog._font_size.value() == 14
        assert dialog._window_width.value() == 1200
        assert dialog._window_height.value() == 800
        assert dialog._history_size.value() == 100
        assert dialog._max_lines.value() == 5000
        assert dialog._auto_save_interval.value() == 5

    def test_apply_settings(self, dialog):
        """测试应用设置."""
        # 修改设置
        dialog._theme_combo.setCurrentIndex(1)
        dialog._font_size.setValue(16)

        # 应用设置
        dialog._apply_settings()

        # 验证设置已收集
        settings = dialog.get_settings()
        assert settings["theme"] == "亮色主题"
        assert settings["font_size"] == 16

    def test_get_settings(self, dialog):
        """测试获取设置."""
        dialog._apply_settings()
        settings = dialog.get_settings()

        assert "theme" in settings
        assert "font_family" in settings
        assert "font_size" in settings
        assert "window_width" in settings
        assert "window_height" in settings
        assert "auto_complete" in settings
        assert "command_history" in settings
        assert "history_size" in settings
        assert "max_lines" in settings
        assert "timestamp" in settings
        assert "auto_save" in settings
        assert "auto_save_interval" in settings
        assert "sound_enabled" in settings
        assert "confirm_quit" in settings

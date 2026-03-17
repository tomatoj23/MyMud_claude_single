"""GUI烟雾测试 - 无头模式快速验证."""

from __future__ import annotations

import os
import sys

import pytest

# 设置无头模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from src.gui.main_window import GUIManager, GameStateSignals, MainWindow


@pytest.fixture
def qapp():
    """Qt应用fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMainWindowSmoke:
    """MainWindow烟雾测试."""

    def test_create_without_engine(self, qapp):
        """测试无引擎创建窗口."""
        window = MainWindow()
        assert window is not None
        assert window.engine is None
        assert window.signals is not None

    def test_create_with_engine(self, qapp, engine):
        """测试有引擎创建窗口."""
        window = MainWindow(engine)
        assert window is not None
        assert window.engine is engine
        assert window.signals is not None

    def test_ui_components_exist(self, qapp):
        """测试UI组件存在."""
        window = MainWindow()

        # 检查面板
        assert hasattr(window, "_output_panel")
        assert window._output_panel is not None

        assert hasattr(window, "_input_panel")
        assert window._input_panel is not None

        assert hasattr(window, "_status_panel")
        assert window._status_panel is not None

        assert hasattr(window, "_right_panel")
        assert window._right_panel is not None

        # 检查状态栏
        assert hasattr(window, "_status_bar")
        assert window._status_bar is not None


class TestGUIManagerSmoke:
    """GUIManager烟雾测试."""

    def test_create_manager(self):
        """测试创建管理器."""
        manager = GUIManager()
        assert manager is not None
        assert manager.main_window is None
        assert manager.player is None

    def test_create_main_window(self, qapp):
        """测试创建主窗口."""
        manager = GUIManager()
        window = manager.create_main_window()
        assert window is not None
        assert manager.main_window is window


class TestGameStateSignalsSmoke:
    """GameStateSignals烟雾测试."""

    def test_signals_exist(self, qapp):
        """测试信号对象存在."""
        signals = GameStateSignals()
        assert signals is not None

        # 检查信号
        assert hasattr(signals, "character_hp_changed")
        assert hasattr(signals, "character_mp_changed")
        assert hasattr(signals, "room_changed")
        assert hasattr(signals, "message_received")
        assert hasattr(signals, "game_started")
        assert hasattr(signals, "game_stopped")

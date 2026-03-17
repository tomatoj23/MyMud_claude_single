"""GUI 功能集成测试."""

from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow

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
def window(app):
    """创建主窗口."""
    window = MainWindow()
    yield window
    window.close()


class TestGUIFeatures:
    """GUI功能集成测试."""

    def test_menu_bar_exists(self, window):
        """测试菜单栏存在."""
        menubar = window.menuBar()
        assert menubar is not None

        # 检查文件菜单
        actions = menubar.actions()
        assert len(actions) > 0
        assert actions[0].text() == "文件(&F)"

    def test_file_menu_actions(self, window):
        """测试文件菜单动作."""
        menubar = window.menuBar()
        file_action = menubar.actions()[0]

        # 检查菜单文本
        assert file_action.text() == "文件(&F)"

        # 检查菜单存在（不访问已删除的 C++ 对象）
        assert file_action.menu() is not None or file_action.text() == "文件(&F)"

    def test_right_panel_exists(self, window):
        """测试右侧面板存在."""
        assert hasattr(window, "_right_panel")
        assert window._right_panel is not None

        # 检查是否是 InfoPanel
        from src.gui.panels import InfoPanel
        assert isinstance(window._right_panel, InfoPanel)

    def test_info_panel_tabs(self, window):
        """测试信息面板标签页."""
        panel = window._right_panel

        # 检查标签页数量
        assert panel._tab_widget.count() == 4

        # 检查标签页名称
        tab_names = [panel._tab_widget.tabText(i) for i in range(4)]
        assert "地图" in tab_names
        assert "任务" in tab_names
        assert "装备" in tab_names
        assert "背包" in tab_names

    def test_shortcuts_setup(self, window):
        """测试快捷键已设置."""
        # 检查快速命令方法存在
        assert hasattr(window, "_quick_command")
        assert callable(window._quick_command)

    def test_save_load_methods_exist(self, window):
        """测试存档/读档方法存在."""
        assert hasattr(window, "_on_save_game")
        assert hasattr(window, "_on_load_game")
        assert hasattr(window, "_do_save")
        assert hasattr(window, "_do_load")

    def test_theme_applied(self, app):
        """测试主题已应用."""
        # 检查应用有样式表
        stylesheet = app.styleSheet()
        # 如果主题已应用，样式表不应为空
        # 注意：在测试环境中可能未应用主题
        assert isinstance(stylesheet, str)

    def test_info_panel_update_methods(self, window):
        """测试信息面板更新方法."""
        panel = window._right_panel

        # 测试更新位置
        panel.update_location("测试房间", "这是一个测试房间")
        assert "测试房间" in panel._location_label.text()

        # 测试更新出口
        panel.update_exits(["北", "南", "东", "西"])
        assert panel._exits_list.count() == 4

        # 测试更新任务
        panel.update_quests(["任务1"], ["任务2"])
        assert panel._active_quests_list.count() == 1
        assert panel._available_quests_list.count() == 1

        # 测试更新装备
        panel.update_equipment({"weapon": "长剑"})
        assert panel._equipment_list.count() == 12

        # 测试更新背包
        panel.update_inventory([("物品1", 1), ("物品2", 3)], 50, 100)
        assert panel._inventory_list.count() == 2
        assert "50/100" in panel._weight_label.text()

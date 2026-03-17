"""设置对话框."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


class SettingsDialog(QDialog):
    """设置对话框."""

    def __init__(self, app: QApplication, parent=None) -> None:
        """初始化设置对话框.

        Args:
            app: Qt应用实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.app = app
        self.settings = {}

        self.setWindowTitle("设置")
        self.resize(500, 400)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QVBoxLayout(self)

        # 标签页
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # 外观标签页
        self._appearance_tab = self._create_appearance_tab()
        self._tab_widget.addTab(self._appearance_tab, "外观")

        # 编辑器标签页
        self._editor_tab = self._create_editor_tab()
        self._tab_widget.addTab(self._editor_tab, "编辑器")

        # 游戏标签页
        self._game_tab = self._create_game_tab()
        self._tab_widget.addTab(self._game_tab, "游戏")

        # 按钮
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._apply_settings
        )
        layout.addWidget(self._button_box)

    def _create_appearance_tab(self) -> QWidget:
        """创建外观标签页."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout(theme_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["暗色主题", "亮色主题"])
        theme_layout.addRow("主题:", self._theme_combo)

        layout.addWidget(theme_group)

        # 字体设置
        font_group = QGroupBox("字体")
        font_layout = QFormLayout(font_group)

        self._font_family = QFontComboBox()
        font_layout.addRow("字体:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 32)
        self._font_size.setValue(14)
        font_layout.addRow("字号:", self._font_size)

        layout.addWidget(font_group)

        # 窗口设置
        window_group = QGroupBox("窗口")
        window_layout = QFormLayout(window_group)

        self._window_width = QSpinBox()
        self._window_width.setRange(800, 2560)
        self._window_width.setValue(1200)
        window_layout.addRow("宽度:", self._window_width)

        self._window_height = QSpinBox()
        self._window_height.setRange(600, 1440)
        self._window_height.setValue(800)
        window_layout.addRow("高度:", self._window_height)

        layout.addWidget(window_group)

        layout.addStretch()
        return widget

    def _create_editor_tab(self) -> QWidget:
        """创建编辑器标签页."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 输入设置
        input_group = QGroupBox("输入")
        input_layout = QFormLayout(input_group)

        self._auto_complete = QCheckBox("启用自动补全")
        input_layout.addRow(self._auto_complete)

        self._command_history = QCheckBox("保存命令历史")
        self._command_history.setChecked(True)
        input_layout.addRow(self._command_history)

        self._history_size = QSpinBox()
        self._history_size.setRange(10, 1000)
        self._history_size.setValue(100)
        input_layout.addRow("历史记录数:", self._history_size)

        layout.addWidget(input_group)

        # 输出设置
        output_group = QGroupBox("输出")
        output_layout = QFormLayout(output_group)

        self._max_lines = QSpinBox()
        self._max_lines.setRange(100, 10000)
        self._max_lines.setValue(5000)
        output_layout.addRow("最大行数:", self._max_lines)

        self._timestamp = QCheckBox("显示时间戳")
        output_layout.addRow(self._timestamp)

        layout.addWidget(output_group)

        layout.addStretch()
        return widget

    def _create_game_tab(self) -> QWidget:
        """创建游戏标签页."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 自动保存设置
        autosave_group = QGroupBox("自动保存")
        autosave_layout = QFormLayout(autosave_group)

        self._auto_save = QCheckBox("启用自动保存")
        autosave_layout.addRow(self._auto_save)

        self._auto_save_interval = QSpinBox()
        self._auto_save_interval.setRange(1, 60)
        self._auto_save_interval.setValue(5)
        self._auto_save_interval.setSuffix(" 分钟")
        autosave_layout.addRow("间隔:", self._auto_save_interval)

        layout.addWidget(autosave_group)

        # 游戏设置
        game_group = QGroupBox("游戏")
        game_layout = QFormLayout(game_group)

        self._sound_enabled = QCheckBox("启用音效")
        game_layout.addRow(self._sound_enabled)

        self._confirm_quit = QCheckBox("退出时确认")
        self._confirm_quit.setChecked(True)
        game_layout.addRow(self._confirm_quit)

        layout.addWidget(game_group)

        layout.addStretch()
        return widget

    def _load_settings(self) -> None:
        """加载设置."""
        # 从配置加载设置
        # 这里使用默认值
        pass

    def _apply_settings(self) -> None:
        """应用设置."""
        # 收集设置
        self.settings = {
            "theme": self._theme_combo.currentText(),
            "font_family": self._font_family.currentFont().family(),
            "font_size": self._font_size.value(),
            "window_width": self._window_width.value(),
            "window_height": self._window_height.value(),
            "auto_complete": self._auto_complete.isChecked(),
            "command_history": self._command_history.isChecked(),
            "history_size": self._history_size.value(),
            "max_lines": self._max_lines.value(),
            "timestamp": self._timestamp.isChecked(),
            "auto_save": self._auto_save.isChecked(),
            "auto_save_interval": self._auto_save_interval.value(),
            "sound_enabled": self._sound_enabled.isChecked(),
            "confirm_quit": self._confirm_quit.isChecked(),
        }

        # 应用主题
        if self.settings["theme"] == "暗色主题":
            self._apply_theme("dark")
        else:
            self._apply_theme("light")

    def _apply_theme(self, theme_name: str) -> None:
        """应用主题.

        Args:
            theme_name: 主题名称
        """
        from src.gui.themes import ThemeManager

        theme_manager = ThemeManager()
        theme_manager.apply_theme(self.app, theme_name)

    def get_settings(self) -> dict:
        """获取设置.

        Returns:
            设置字典
        """
        return self.settings

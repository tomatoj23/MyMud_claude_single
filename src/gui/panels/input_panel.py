"""输入面板."""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class InputPanel(QWidget):
    """输入面板.

    包含输入框和发送按钮。
    """

    def __init__(self, font: QFont | None = None, parent: QWidget | None = None) -> None:
        """初始化输入面板.

        Args:
            font: 字体
            parent: 父窗口
        """
        super().__init__(parent)
        self._font = font or QFont("Microsoft YaHei", 14)
        self._submit_callback: Callable[[str], None] | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 输入框
        self._input_field = QLineEdit()
        self._input_field.setFont(self._font)
        self._input_field.setPlaceholderText("输入命令...")
        self._input_field.returnPressed.connect(self._on_submit)
        layout.addWidget(self._input_field)

        # 发送按钮
        self._send_button = QPushButton("发送")
        self._send_button.clicked.connect(self._on_submit)
        layout.addWidget(self._send_button)

    def _on_submit(self) -> None:
        """处理提交."""
        text = self._input_field.text().strip()
        if text and self._submit_callback:
            self._submit_callback(text)

    def set_submit_callback(self, callback: Callable[[str], None]) -> None:
        """设置提交回调.

        Args:
            callback: 回调函数
        """
        self._submit_callback = callback

    def clear(self) -> None:
        """清空输入."""
        self._input_field.clear()

    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态.

        Args:
            enabled: 是否启用
        """
        self._input_field.setEnabled(enabled)
        self._send_button.setEnabled(enabled)

    def set_focus(self) -> None:
        """设置焦点."""
        self._input_field.setFocus()

    def set_font(self, font: QFont) -> None:
        """设置字体.

        Args:
            font: 字体
        """
        self._font = font
        self._input_field.setFont(font)

    def set_text(self, text: str) -> None:
        """设置文本.

        Args:
            text: 文本内容
        """
        self._input_field.setText(text)

    def text(self) -> str:
        """获取文本.

        Returns:
            文本内容
        """
        return self._input_field.text()

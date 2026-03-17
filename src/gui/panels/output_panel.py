"""输出面板."""

from __future__ import annotations

from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget


class OutputPanel(QWidget):
    """输出面板.

    显示游戏输出信息。
    """

    MAX_BLOCKS = 5000

    def __init__(self, font: QFont | None = None, parent: QWidget | None = None) -> None:
        """初始化输出面板.

        Args:
            font: 字体
            parent: 父窗口
        """
        super().__init__(parent)
        self._font = font or QFont("Microsoft YaHei", 14)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._browser = QTextBrowser()
        self._browser.setFont(self._font)
        self._browser.setOpenExternalLinks(False)
        layout.addWidget(self._browser)

    def append(self, html: str) -> None:
        """追加HTML内容.

        Args:
            html: HTML内容
        """
        self._browser.append(html)

        # 限制最大行数
        doc = self._browser.document()
        if doc.blockCount() > self.MAX_BLOCKS:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                doc.blockCount() - self.MAX_BLOCKS,
            )
            cursor.removeSelectedText()

    def clear(self) -> None:
        """清空内容."""
        self._browser.clear()

    def set_font(self, font: QFont) -> None:
        """设置字体.

        Args:
            font: 字体
        """
        self._font = font
        self._browser.setFont(font)

    def set_max_blocks(self, max_blocks: int) -> None:
        """设置最大行数.

        Args:
            max_blocks: 最大行数
        """
        self.MAX_BLOCKS = max_blocks

"""主题管理器."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


class ThemeManager:
    """主题管理器.

    负责加载和应用QSS样式主题。
    """

    def __init__(self) -> None:
        """初始化主题管理器."""
        self._current_theme = "dark"
        self._themes_dir = Path(__file__).parent

    def apply_theme(self, app: QApplication, theme_name: str = "dark") -> None:
        """应用主题.

        Args:
            app: Qt应用实例
            theme_name: 主题名称
        """
        theme_file = self._themes_dir / f"{theme_name}.qss"

        if not theme_file.exists():
            return

        with open(theme_file, "r", encoding="utf-8") as f:
            qss = f.read()

        app.setStyleSheet(qss)
        self._current_theme = theme_name

    @property
    def current_theme(self) -> str:
        """获取当前主题名称."""
        return self._current_theme

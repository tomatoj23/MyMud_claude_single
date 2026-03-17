"""状态面板."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class StatusPanel(QWidget):
    """左侧状态面板.

    显示角色状态信息：
    - 当前房间
    - HP进度条
    - MP进度条
    - 状态标签
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化状态面板.

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QVBoxLayout(self)

        # 房间标签
        self._room_label = QLabel("房间: 未知")
        layout.addWidget(self._room_label)

        # HP进度条
        self._hp_bar = QProgressBar()
        self._hp_bar.setFormat("气血: %v/%m")
        layout.addWidget(self._hp_bar)

        # MP进度条
        self._mp_bar = QProgressBar()
        self._mp_bar.setFormat("内力: %v/%m")
        layout.addWidget(self._mp_bar)

        # 状态标签
        self._status_label = QLabel("状态: 正常")
        layout.addWidget(self._status_label)

        layout.addStretch()

    def update_room(self, room_name: str) -> None:
        """更新房间信息.

        Args:
            room_name: 房间名称
        """
        self._room_label.setText(f"房间: {room_name}")

    def update_hp(self, current: int, maximum: int) -> None:
        """更新HP.

        Args:
            current: 当前值
            maximum: 最大值
        """
        self._hp_bar.setMaximum(maximum)
        self._hp_bar.setValue(current)

    def update_mp(self, current: int, maximum: int) -> None:
        """更新MP.

        Args:
            current: 当前值
            maximum: 最大值
        """
        self._mp_bar.setMaximum(maximum)
        self._mp_bar.setValue(current)

    def update_status(self, status: str) -> None:
        """更新状态.

        Args:
            status: 状态文本
        """
        self._status_label.setText(f"状态: {status}")

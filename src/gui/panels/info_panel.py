"""右侧信息面板.

包含地图、任务、装备等信息展示.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class InfoPanel(QWidget):
    """右侧信息面板.

    包含多个标签页：
    - 地图：显示当前位置和出口
    - 任务：显示当前任务列表
    - 装备：显示当前装备
    - 背包：显示背包物品
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化信息面板.

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """设置界面布局."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # 地图标签页
        self._map_tab = self._create_map_tab()
        self._tab_widget.addTab(self._map_tab, "地图")

        # 任务标签页
        self._quest_tab = self._create_quest_tab()
        self._tab_widget.addTab(self._quest_tab, "任务")

        # 装备标签页
        self._equipment_tab = self._create_equipment_tab()
        self._tab_widget.addTab(self._equipment_tab, "装备")

        # 背包标签页
        self._inventory_tab = self._create_inventory_tab()
        self._tab_widget.addTab(self._inventory_tab, "背包")

    def _create_map_tab(self) -> QWidget:
        """创建地图标签页.

        Returns:
            地图标签页窗口
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 当前位置
        location_group = QGroupBox("当前位置")
        location_layout = QVBoxLayout(location_group)

        self._location_label = QLabel("未知")
        self._location_label.setWordWrap(True)
        location_layout.addWidget(self._location_label)

        layout.addWidget(location_group)

        # 出口列表
        exits_group = QGroupBox("出口")
        exits_layout = QVBoxLayout(exits_group)

        self._exits_list = QListWidget()
        exits_layout.addWidget(self._exits_list)

        layout.addWidget(exits_group)

        layout.addStretch()
        return widget

    def _create_quest_tab(self) -> QWidget:
        """创建任务标签页.

        Returns:
            任务标签页窗口
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 进行中的任务
        active_group = QGroupBox("进行中")
        active_layout = QVBoxLayout(active_group)

        self._active_quests_list = QListWidget()
        active_layout.addWidget(self._active_quests_list)

        layout.addWidget(active_group)

        # 可接任务
        available_group = QGroupBox("可接任务")
        available_layout = QVBoxLayout(available_group)

        self._available_quests_list = QListWidget()
        available_layout.addWidget(self._available_quests_list)

        layout.addWidget(available_group)

        return widget

    def _create_equipment_tab(self) -> QWidget:
        """创建装备标签页.

        Returns:
            装备标签页窗口
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 装备列表
        self._equipment_list = QListWidget()
        layout.addWidget(self._equipment_list)

        # 装备槽位
        slots = [
            "武器", "头部", "身体", "手部(左)", "手部(右)",
            "腿部", "脚部", "戒指1", "戒指2", "项链", "披风", "腰带"
        ]

        for slot in slots:
            item = QListWidgetItem(f"{slot}: 无")
            self._equipment_list.addItem(item)

        return widget

    def _create_inventory_tab(self) -> QWidget:
        """创建背包标签页.

        Returns:
            背包标签页窗口
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 背包列表
        self._inventory_list = QListWidget()
        layout.addWidget(self._inventory_list)

        # 负重信息
        self._weight_label = QLabel("负重: 0/100")
        layout.addWidget(self._weight_label)

        return widget

    def update_location(self, room_name: str, description: str) -> None:
        """更新位置信息.

        Args:
            room_name: 房间名称
            description: 房间描述
        """
        self._location_label.setText(f"{room_name}\n\n{description}")

    def update_exits(self, exits: list[str]) -> None:
        """更新出口列表.

        Args:
            exits: 出口列表
        """
        self._exits_list.clear()
        for exit_name in exits:
            self._exits_list.addItem(exit_name)

    def update_quests(self, active: list[str], available: list[str]) -> None:
        """更新任务列表.

        Args:
            active: 进行中的任务
            available: 可接任务
        """
        self._active_quests_list.clear()
        for quest in active:
            self._active_quests_list.addItem(quest)

        self._available_quests_list.clear()
        for quest in available:
            self._available_quests_list.addItem(quest)

    def update_equipment(self, equipment: dict[str, str]) -> None:
        """更新装备信息.

        Args:
            equipment: 装备字典，键为槽位，值为装备名称
        """
        slots = [
            ("weapon", "武器"),
            ("head", "头部"),
            ("body", "身体"),
            ("hand_left", "手部(左)"),
            ("hand_right", "手部(右)"),
            ("legs", "腿部"),
            ("feet", "脚部"),
            ("ring1", "戒指1"),
            ("ring2", "戒指2"),
            ("neck", "项链"),
            ("cloak", "披风"),
            ("belt", "腰带"),
        ]

        self._equipment_list.clear()
        for slot_key, slot_name in slots:
            item_name = equipment.get(slot_key, "无")
            item = QListWidgetItem(f"{slot_name}: {item_name}")
            self._equipment_list.addItem(item)

    def update_inventory(self, items: list[tuple[str, int]], weight: int, max_weight: int) -> None:
        """更新背包信息.

        Args:
            items: 物品列表，每项为(物品名, 数量)
            weight: 当前负重
            max_weight: 最大负重
        """
        self._inventory_list.clear()
        for item_name, count in items:
            if count > 1:
                self._inventory_list.addItem(f"{item_name} x{count}")
            else:
                self._inventory_list.addItem(item_name)

        self._weight_label.setText(f"负重: {weight}/{max_weight}")

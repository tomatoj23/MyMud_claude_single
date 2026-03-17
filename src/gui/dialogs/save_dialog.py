"""存档/读档对话框."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from src.engine.save import SaveInfo, SaveManager


class SaveDialog(QDialog):
    """存档对话框."""

    def __init__(self, save_manager: SaveManager, parent=None) -> None:
        """初始化存档对话框.

        Args:
            save_manager: 存档管理器
            parent: 父窗口
        """
        super().__init__(parent)
        self.save_manager = save_manager
        self.selected_slot: str | None = None

        self.setWindowTitle("保存游戏")
        self.resize(500, 400)

        self._setup_ui()
        self._load_saves()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QVBoxLayout(self)

        # 存档列表
        list_label = QLabel("选择存档槽位：")
        layout.addWidget(list_label)

        self._save_list = QListWidget()
        self._save_list.itemClicked.connect(self._on_save_selected)
        layout.addWidget(self._save_list)

        # 存档名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("存档名称：")
        name_layout.addWidget(name_label)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("输入存档名称...")
        name_layout.addWidget(self._name_input)

        layout.addLayout(name_layout)

        # 按钮
        button_layout = QHBoxLayout()

        self._new_button = QPushButton("新建存档")
        self._new_button.clicked.connect(self._on_new_save)
        button_layout.addWidget(self._new_button)

        button_layout.addStretch()

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_save)
        self._button_box.rejected.connect(self.reject)
        button_layout.addWidget(self._button_box)

        layout.addLayout(button_layout)

    def _load_saves(self) -> None:
        """加载存档列表."""
        self._save_list.clear()

        saves = self.save_manager.list_saves()
        for save_info in saves:
            item_text = f"{save_info.name} - {save_info.timestamp[:19]} - Lv.{save_info.level}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, save_info.slot)
            self._save_list.addItem(item)

    def _on_save_selected(self, item: QListWidgetItem) -> None:
        """处理存档选择.

        Args:
            item: 列表项
        """
        self.selected_slot = item.data(Qt.ItemDataRole.UserRole)
        save_info = self.save_manager.get_save_info(self.selected_slot)
        if save_info:
            self._name_input.setText(save_info.name)

    def _on_new_save(self) -> None:
        """创建新存档."""
        # 生成新槽位
        existing_slots = [save.slot for save in self.save_manager.list_saves()]
        slot_num = 1
        while f"slot_{slot_num}" in existing_slots:
            slot_num += 1

        self.selected_slot = f"slot_{slot_num}"
        self._name_input.setText(f"存档 {slot_num}")
        self._name_input.setFocus()

    def _on_save(self) -> None:
        """执行保存."""
        if not self.selected_slot:
            QMessageBox.warning(self, "警告", "请选择或创建一个存档槽位")
            return

        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入存档名称")
            return

        # 确认覆盖
        if self.save_manager.get_save_info(self.selected_slot):
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                f"存档 '{name}' 已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.accept()

    def get_save_params(self) -> tuple[str, str]:
        """获取保存参数.

        Returns:
            (槽位, 名称)
        """
        return self.selected_slot or "", self._name_input.text().strip()


class LoadDialog(QDialog):
    """读档对话框."""

    def __init__(self, save_manager: SaveManager, parent=None) -> None:
        """初始化读档对话框.

        Args:
            save_manager: 存档管理器
            parent: 父窗口
        """
        super().__init__(parent)
        self.save_manager = save_manager
        self.selected_slot: str | None = None

        self.setWindowTitle("读取游戏")
        self.resize(500, 400)

        self._setup_ui()
        self._load_saves()

    def _setup_ui(self) -> None:
        """设置界面."""
        layout = QVBoxLayout(self)

        # 存档列表
        list_label = QLabel("选择要读取的存档：")
        layout.addWidget(list_label)

        self._save_list = QListWidget()
        self._save_list.itemClicked.connect(self._on_save_selected)
        self._save_list.itemDoubleClicked.connect(self._on_load)
        layout.addWidget(self._save_list)

        # 存档详情
        self._detail_label = QLabel("选择一个存档查看详情")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        # 按钮
        button_layout = QHBoxLayout()

        self._delete_button = QPushButton("删除")
        self._delete_button.clicked.connect(self._on_delete)
        self._delete_button.setEnabled(False)
        button_layout.addWidget(self._delete_button)

        button_layout.addStretch()

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_load)
        self._button_box.rejected.connect(self.reject)
        button_layout.addWidget(self._button_box)

        layout.addLayout(button_layout)

    def _load_saves(self) -> None:
        """加载存档列表."""
        self._save_list.clear()

        saves = self.save_manager.list_saves()
        if not saves:
            item = QListWidgetItem("没有可用的存档")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._save_list.addItem(item)
            return

        for save_info in saves:
            item_text = f"{save_info.name} - {save_info.timestamp[:19]} - Lv.{save_info.level}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, save_info.slot)
            self._save_list.addItem(item)

    def _on_save_selected(self, item: QListWidgetItem) -> None:
        """处理存档选择.

        Args:
            item: 列表项
        """
        self.selected_slot = item.data(Qt.ItemDataRole.UserRole)
        if not self.selected_slot:
            return

        save_info = self.save_manager.get_save_info(self.selected_slot)
        if save_info:
            details = (
                f"名称: {save_info.name}\n"
                f"时间: {save_info.timestamp[:19]}\n"
                f"等级: {save_info.level}\n"
                f"位置: {save_info.location}\n"
                f"游戏时长: {save_info.play_time // 60} 分钟\n"
                f"文件大小: {save_info.compressed_size / 1024:.1f} KB"
            )
            self._detail_label.setText(details)
            self._delete_button.setEnabled(True)

    def _on_delete(self) -> None:
        """删除存档."""
        if not self.selected_slot:
            return

        save_info = self.save_manager.get_save_info(self.selected_slot)
        if not save_info:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除存档 '{save_info.name}' 吗？\n此操作无法撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.save_manager.delete_save(self.selected_slot)
            self._load_saves()
            self.selected_slot = None
            self._detail_label.setText("选择一个存档查看详情")
            self._delete_button.setEnabled(False)

    def _on_load(self) -> None:
        """执行读取."""
        if not self.selected_slot:
            QMessageBox.warning(self, "警告", "请选择一个存档")
            return

        self.accept()

    def get_selected_slot(self) -> str | None:
        """获取选中的槽位.

        Returns:
            槽位名称
        """
        return self.selected_slot

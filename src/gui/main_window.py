"""PySide6主窗口.

提供游戏的主界面框架和状态管理.
"""

from __future__ import annotations

import asyncio
import html as html_mod
import sys
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.engine.core.messages import Message, MessageType
from src.gui.panels import InfoPanel, InputPanel, OutputPanel, StatusPanel
from src.gui.utils import AnimationHelper, RichTextFormatter
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine
    from src.game.typeclasses.character import Character

logger = get_logger(__name__)


class GameStateSignals(QObject):
    """游戏状态信号中心.

    用于引擎事件到GUI的异步通信.
    """

    # 角色状态变更
    character_hp_changed = Signal(int, int)  # 当前值, 最大值
    character_mp_changed = Signal(int, int)
    character_exp_changed = Signal(int, int)
    character_level_changed = Signal(int)

    # 房间变更
    room_changed = Signal(str, str)  # 房间名, 描述

    # 消息输出
    message_received = Signal(str, str)  # 消息类型, 内容

    # 装备变更
    equipment_changed = Signal()

    # 背包变更
    inventory_changed = Signal()

    # 任务变更
    quest_changed = Signal()

    # 游戏状态
    game_started = Signal()
    game_stopped = Signal()


class MainWindow(QMainWindow):
    """游戏主窗口.

    Attributes:
        engine: 游戏引擎实例
        signals: 游戏状态信号
        gui_manager: GUI管理器引用
    """

    MAX_OUTPUT_BLOCKS = 5000

    def __init__(
        self,
        engine: Optional["GameEngine"] = None,
        gui_manager: Optional["GUIManager"] = None,
    ) -> None:
        """初始化主窗口.

        Args:
            engine: 游戏引擎实例
            gui_manager: GUI管理器引用
        """
        super().__init__()

        self.engine = engine
        self.gui_manager = gui_manager
        self.signals = GameStateSignals()
        self._subscribed = False

        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._setup_menu()

        # 启动时淡入动画（可选，通过配置启用）
        # fade_in = AnimationHelper.fade_in(self, duration=500)
        # fade_in.start()

    def _setup_ui(self) -> None:
        """设置界面布局."""
        # 从配置读取窗口尺寸
        if self.engine:
            config = self.engine.config.gui
            self.setWindowTitle(self.engine.config.game.name)
            self.resize(config.window_width, config.window_height)
            font = QFont(config.font_family, config.font_size)
        else:
            self.setWindowTitle("金庸武侠MUD")
            self.resize(1200, 800)
            font = QFont("Microsoft YaHei", 14)

        # 中央部件
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)

        # 主布局
        self._main_layout = QVBoxLayout(self._central_widget)

        # 分割器布局
        self._splitter = QSplitter()
        self._main_layout.addWidget(self._splitter)

        # 左侧面板 - 角色状态
        self._status_panel = StatusPanel()
        self._splitter.addWidget(self._status_panel)

        # 中间面板 - 主输出和输入
        self._center_panel = QWidget()
        self._center_layout = QVBoxLayout(self._center_panel)
        self._center_layout.setContentsMargins(0, 0, 0, 0)
        self._splitter.addWidget(self._center_panel)

        # 输出面板
        self._output_panel = OutputPanel(font)
        self._center_layout.addWidget(self._output_panel)

        # 输入面板
        self._input_panel = InputPanel(font)
        self._input_panel.set_submit_callback(self._on_submit_command)
        self._center_layout.addWidget(self._input_panel)

        # 右侧面板 - 地图/任务
        self._right_panel = InfoPanel()
        self._splitter.addWidget(self._right_panel)

        # 设置分割比例
        self._splitter.setSizes([250, 700, 250])

        # 底部状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("初始化中...")

    def _connect_signals(self) -> None:
        """连接信号与槽."""
        # 游戏状态信号
        self.signals.game_started.connect(self._on_game_started)
        self.signals.game_stopped.connect(self._on_game_stopped)

        # 角色状态信号
        self.signals.character_hp_changed.connect(self._on_hp_changed)
        self.signals.character_mp_changed.connect(self._on_mp_changed)
        self.signals.room_changed.connect(self._on_room_changed)
        self.signals.equipment_changed.connect(self._on_equipment_changed)
        self.signals.inventory_changed.connect(self._on_inventory_changed)
        self.signals.quest_changed.connect(self._on_quest_changed)

        # 消息信号
        self.signals.message_received.connect(self._on_message_received)

        # MessageBus订阅
        if self.engine and not self._subscribed:
            self.engine.message_bus.subscribe(self._on_message)
            self.engine.message_bus.subscribe_status("character", self._on_status_update)
            self._subscribed = True

    def _setup_shortcuts(self) -> None:
        """设置快捷键."""
        # 输入焦点快捷键
        focus_input = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_input.activated.connect(self._input_panel.set_focus)

        # 清空输出区快捷键
        clear_output = QShortcut(QKeySequence("Ctrl+K"), self)
        clear_output.activated.connect(self._output_panel.clear)

        # 退出快捷键
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

        # 常用命令快捷键
        look_shortcut = QShortcut(QKeySequence("F1"), self)
        look_shortcut.activated.connect(lambda: self._quick_command("look"))

        inventory_shortcut = QShortcut(QKeySequence("F2"), self)
        inventory_shortcut.activated.connect(lambda: self._quick_command("inventory"))

        status_shortcut = QShortcut(QKeySequence("F3"), self)
        status_shortcut.activated.connect(lambda: self._quick_command("status"))

    def _quick_command(self, command: str) -> None:
        """快速执行命令.

        Args:
            command: 命令文本
        """
        self._input_panel.set_text(command)
        self._on_submit_command(command)

    def _setup_menu(self) -> None:
        """设置菜单栏."""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        save_action = file_menu.addAction("保存游戏(&S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_game)

        load_action = file_menu.addAction("读取游戏(&L)")
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_game)

        file_menu.addSeparator()

        settings_action = file_menu.addAction("设置(&P)")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._on_settings)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("退出(&Q)")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

    def _on_save_game(self) -> None:
        """处理保存游戏."""
        if not self.engine:
            QMessageBox.warning(self, "错误", "游戏引擎未初始化")
            return

        try:
            from src.engine.save import SaveManager
            from src.gui.dialogs import SaveDialog

            save_manager = SaveManager(self.engine)
            dialog = SaveDialog(save_manager, self)

            if dialog.exec():
                slot, name = dialog.get_save_params()
                if slot:
                    import asyncio
                    asyncio.create_task(self._do_save(save_manager, slot, name))

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存游戏时出错:\n{e}")

    async def _do_save(self, save_manager, slot: str, name: str) -> None:
        """执行保存操作.

        Args:
            save_manager: 存档管理器
            slot: 槽位
            name: 名称
        """
        try:
            await save_manager.save(slot, name)
            self.engine.message_bus.emit_text(
                MessageType.SYSTEM, f"游戏已保存到 '{name}'"
            )
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存游戏时出错:\n{e}")

    def _on_load_game(self) -> None:
        """处理读取游戏."""
        if not self.engine:
            QMessageBox.warning(self, "错误", "游戏引擎未初始化")
            return

        try:
            from src.engine.save import SaveManager
            from src.gui.dialogs import LoadDialog

            save_manager = SaveManager(self.engine)
            dialog = LoadDialog(save_manager, self)

            if dialog.exec():
                slot = dialog.get_selected_slot()
                if slot:
                    import asyncio
                    asyncio.create_task(self._do_load(save_manager, slot))

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"读取游戏时出错:\n{e}")

    async def _do_load(self, save_manager, slot: str) -> None:
        """执行读取操作.

        Args:
            save_manager: 存档管理器
            slot: 槽位
        """
        try:
            save_data = await save_manager.load(slot)
            self.engine.message_bus.emit_text(
                MessageType.SYSTEM, f"游戏已读取: {save_data['name']}"
            )

            # 更新GUI状态
            if self.gui_manager and hasattr(self.engine, "_player_ref"):
                player = self.engine._player_ref
                if player:
                    self.gui_manager.set_player(player)
                    self.gui_manager.update_from_character(player)

        except FileNotFoundError:
            QMessageBox.warning(self, "读取失败", "存档文件不存在")
        except ValueError as e:
            QMessageBox.critical(self, "读取失败", f"存档文件损坏或版本不兼容:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"读取游戏时出错:\n{e}")

    def _on_settings(self) -> None:
        """处理设置."""
        try:
            from src.gui.dialogs import SettingsDialog

            dialog = SettingsDialog(QApplication.instance(), self)

            if dialog.exec():
                settings = dialog.get_settings()
                # 应用设置
                self._apply_settings(settings)

        except Exception as e:
            QMessageBox.critical(self, "设置失败", f"打开设置时出错:\n{e}")

    def _apply_settings(self, settings: dict) -> None:
        """应用设置.

        Args:
            settings: 设置字典
        """
        # 应用字体设置
        if "font_family" in settings and "font_size" in settings:
            from PySide6.QtGui import QFont
            font = QFont(settings["font_family"], settings["font_size"])
            self._output_panel.set_font(font)
            self._input_panel.set_font(font)

        # 应用输出行数限制
        if "max_lines" in settings:
            self._output_panel.set_max_blocks(settings["max_lines"])

        # 显示应用成功消息
        if self.engine:
            self.engine.message_bus.emit_text(
                MessageType.SYSTEM, "设置已应用"
            )

    def _on_message(self, message: Message) -> None:
        """处理MessageBus消息.

        Args:
            message: 消息对象
        """
        self.signals.message_received.emit(message.msg_type.value, message.content)

    def _on_status_update(self, data: dict) -> None:
        """处理状态更新.

        Args:
            data: 状态数据
        """
        if "hp" in data:
            current, max_val = data["hp"]
            self.signals.character_hp_changed.emit(current, max_val)
        if "mp" in data:
            current, max_val = data["mp"]
            self.signals.character_mp_changed.emit(current, max_val)

    def _on_message_received(self, msg_type: str, content: str) -> None:
        """处理消息接收信号.

        Args:
            msg_type: 消息类型
            content: 消息内容
        """
        # 使用富文本格式化器
        html = RichTextFormatter.format_message(msg_type, content)
        self._output_panel.append(html)

    def _on_hp_changed(self, current: int, max_val: int) -> None:
        """处理HP变化.

        Args:
            current: 当前值
            max_val: 最大值
        """
        self._status_panel.update_hp(current, max_val)

    def _on_mp_changed(self, current: int, max_val: int) -> None:
        """处理MP变化.

        Args:
            current: 当前值
            max_val: 最大值
        """
        self._status_panel.update_mp(current, max_val)

    def _on_room_changed(self, name: str, description: str) -> None:
        """处理房间变化.

        Args:
            name: 房间名称
            description: 房间描述
        """
        self._status_panel.update_room(name)

        # 更新右侧面板的位置信息
        self._right_panel.update_location(name, description)

        # 更新出口列表
        if self.gui_manager and self.gui_manager.player:
            room = self.gui_manager.player.location
            if room:
                exits = list(room.exits.keys()) if hasattr(room, 'exits') else []
                self._right_panel.update_exits(exits)

    def _on_equipment_changed(self) -> None:
        """处理装备变化."""
        if not self.gui_manager or not self.gui_manager.player:
            return

        player = self.gui_manager.player
        equipment_dict = {}

        # 获取装备信息
        if hasattr(player, 'equipment_get_all'):
            equipment_dict = player.equipment_get_all()

        self._right_panel.update_equipment(equipment_dict)

    def _on_inventory_changed(self) -> None:
        """处理背包变化."""
        if not self.gui_manager or not self.gui_manager.player:
            return

        player = self.gui_manager.player
        items = []
        weight = 0
        max_weight = 100

        # 获取背包物品
        if hasattr(player, 'contents'):
            for item in player.contents:
                item_name = getattr(item, 'name', str(item))
                items.append((item_name, 1))

        # 获取负重信息
        if hasattr(player, 'db') and hasattr(player.db, 'carry_weight'):
            weight = player.db.carry_weight or 0
        if hasattr(player, 'db') and hasattr(player.db, 'max_carry_weight'):
            max_weight = player.db.max_carry_weight or 100

        self._right_panel.update_inventory(items, weight, max_weight)

    def _on_quest_changed(self) -> None:
        """处理任务变化."""
        if not self.gui_manager or not self.gui_manager.player:
            return

        player = self.gui_manager.player
        active_quests = []
        available_quests = []

        # 获取任务信息
        if hasattr(player, 'quest_get_active'):
            active_quests = [q.name for q in player.quest_get_active()]
        if hasattr(player, 'quest_get_available'):
            available_quests = [q.name for q in player.quest_get_available()]

        self._right_panel.update_quests(active_quests, available_quests)

    def _on_submit_command(self, text: str = "") -> None:
        """处理命令提交.

        Args:
            text: 命令文本（可选）
        """
        if not text:
            text = self._input_panel.text().strip()

        if not text:
            return

        # 清空输入框
        self._input_panel.clear()

        # 禁用输入
        self._input_panel.set_enabled(False)

        # 回显命令
        self._output_panel.append(
            f'<span style="color: #999999;">&gt; {html_mod.escape(text)}</span>'
        )

        # 异步执行命令
        asyncio.ensure_future(self._execute_command(text))

    async def _execute_command(self, text: str) -> None:
        """执行命令.

        Args:
            text: 命令文本
        """
        try:
            if self.engine and self.gui_manager and self.gui_manager.player:
                await self.engine.process_input(self.gui_manager.player, text)
        except Exception as e:
            logger.exception(f"命令执行错误: {e}")
            self.engine.message_bus.emit_text(MessageType.ERROR, f"命令执行错误: {e}")
        finally:
            # 重新启用输入
            self._input_panel.set_enabled(True)
            self._input_panel.set_focus()

    def _on_game_started(self) -> None:
        """游戏启动回调."""
        self._status_bar.showMessage("游戏运行中")
        self._input_panel.set_enabled(True)
        self._input_panel.set_focus()

    def _on_game_stopped(self) -> None:
        """游戏停止回调."""
        self._status_bar.showMessage("游戏已停止")
        self._input_panel.set_enabled(False)

    def closeEvent(self, event) -> None:
        """窗口关闭事件.

        Args:
            event: 关闭事件
        """
        # 禁用输入
        self._input_panel.set_enabled(False)
        self._status_bar.showMessage("正在关闭...")

        # 取消MessageBus订阅
        if self.engine and self._subscribed:
            self.engine.message_bus.unsubscribe(self._on_message)
            self.engine.message_bus.unsubscribe_status("character", self._on_status_update)
            self._subscribed = False

        # 停止引擎
        if self.engine and self.engine.running:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建一个任务来停止引擎
                asyncio.create_task(self.engine.stop())
            else:
                # 如果事件循环未运行，同步停止
                loop.run_until_complete(self.engine.stop())

        event.accept()

    def update_character_status(self, hp: int, max_hp: int, mp: int, max_mp: int) -> None:
        """更新角色状态显示.

        Args:
            hp: 当前气血
            max_hp: 最大气血
            mp: 当前内力
            max_mp: 最大内力
        """
        self.signals.character_hp_changed.emit(hp, max_hp)
        self.signals.character_mp_changed.emit(mp, max_mp)

    def update_room(self, name: str, description: str) -> None:
        """更新房间显示.

        Args:
            name: 房间名称
            description: 房间描述
        """
        self.signals.room_changed.emit(name, description)

    def append_message(self, msg_type: str, message: str) -> None:
        """追加消息到输出区域.

        Args:
            msg_type: 消息类型 (system/chat/combat)
            message: 消息内容
        """
        self.signals.message_received.emit(msg_type, message)


class GUIManager:
    """GUI管理器.

    管理GUI生命周期和与引擎的交互.
    """

    def __init__(self) -> None:
        """初始化GUI管理器."""
        self._main_window: Optional[MainWindow] = None
        self._engine: Optional["GameEngine"] = None
        self._player: Optional["Character"] = None

    def create_main_window(self, engine: Optional["GameEngine"] = None) -> MainWindow:
        """创建主窗口.

        Args:
            engine: 游戏引擎实例

        Returns:
            主窗口实例
        """
        self._engine = engine
        self._main_window = MainWindow(engine, self)
        return self._main_window

    @property
    def main_window(self) -> Optional[MainWindow]:
        """获取主窗口."""
        return self._main_window

    @property
    def player(self) -> Optional["Character"]:
        """获取玩家角色."""
        return self._player

    def set_player(self, player: "Character") -> None:
        """设置玩家角色.

        Args:
            player: 玩家角色对象
        """
        self._player = player

    def update_from_character(self, character: "Character") -> None:
        """从角色对象更新GUI.

        Args:
            character: 角色对象
        """
        if not self._main_window:
            return

        # 更新状态
        hp, max_hp = character.get_hp()
        mp, max_mp = character.get_mp()
        self._main_window.update_character_status(hp, max_hp, mp, max_mp)

        # 更新房间
        if character.location:
            self._main_window.update_room(
                character.location.key, character.location.description
            )


async def _setup_default_session(engine: "GameEngine") -> "Character":
    """设置默认游戏会话.

    Args:
        engine: 游戏引擎实例

    Returns:
        默认玩家角色
    """
    # 创建默认房间
    room = await engine.objects.create(
        typeclass_path="src.game.typeclasses.room.Room",
        key="客栈大堂",
        attributes={
            "description": "这是一间宽敞的客栈大堂，四周摆放着几张木桌。",
            "coords": (0, 0, 0),
        },
    )

    # 创建默认玩家
    player = await engine.objects.create(
        typeclass_path="src.game.typeclasses.character.Character",
        key="少侠",
        attributes={"location_id": room.id},
    )

    # 设置玩家的location
    player._db_model.location_id = room.id

    # 挂载message_bus
    player.message_bus = engine.message_bus

    logger.info(f"默认会话已创建: 玩家={player.key}, 房间={room.key}")
    return player


def main() -> None:
    """GUI主入口."""
    try:
        # 创建Qt应用
        app = QApplication(sys.argv)

        # 应用主题
        from src.gui.themes import ThemeManager
        theme_manager = ThemeManager()
        theme_manager.apply_theme(app, "dark")

        # 创建qasync事件循环
        import qasync

        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        _engine_ref = None

        async def async_main():
            """异步主函数."""
            nonlocal _engine_ref
            try:
                # 加载配置
                from src.utils.config import load_config

                config = load_config()

                # 创建调度器
                from src.engine.events.qt_scheduler import FlexibleEventScheduler

                scheduler = FlexibleEventScheduler(backend="hybrid")

                # 创建引擎
                from src.engine.core.engine import create_engine

                engine = create_engine(config)
                engine._injected_scheduler = scheduler

                # 初始化引擎
                await engine.initialize()

                # 启动引擎
                await engine.start()

                # 保存引擎引用用于关闭时清理
                _engine_ref = engine

                # 创建默认会话
                player = await _setup_default_session(engine)

                # 创建GUI
                gui_manager = GUIManager()
                window = gui_manager.create_main_window(engine)
                gui_manager.set_player(player)

                # 更新初始状态
                gui_manager.update_from_character(player)

                # 显示窗口
                window.show()
                window.signals.game_started.emit()

                # 发送欢迎消息
                engine.message_bus.emit_text(
                    MessageType.SYSTEM, f"欢迎来到{config.game.name}！"
                )
                engine.message_bus.emit_text(MessageType.INFO, "输入 'look' 查看周围环境")

            except Exception as e:
                logger.exception(f"初始化失败: {e}")
                QMessageBox.critical(
                    None, "初始化错误", f"游戏初始化失败:\n{e}"
                )
                sys.exit(1)

        # 运行异步初始化
        loop.run_until_complete(async_main())

        # 进入事件循环
        with loop:
            loop.run_forever()

        # 关闭引擎（确保完整清理）
        if _engine_ref and _engine_ref.running:
            loop.run_until_complete(_engine_ref.stop())

    except Exception as e:
        logger.exception(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


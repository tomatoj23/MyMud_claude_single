"""PySide6主窗口.

提供游戏的主界面框架和状态管理.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine


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
    
    # 游戏状态
    game_started = Signal()
    game_stopped = Signal()


class MainWindow(QMainWindow):
    """游戏主窗口.
    
    Attributes:
        engine: 游戏引擎实例
        signals: 游戏状态信号
    """
    
    def __init__(self, engine: Optional["GameEngine"] = None) -> None:
        """初始化主窗口.
        
        Args:
            engine: 游戏引擎实例
        """
        super().__init__()
        
        self.engine = engine
        self.signals = GameStateSignals()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """设置界面布局."""
        self.setWindowTitle("金庸武侠MUD")
        self.resize(1200, 800)
        
        # 中央部件
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        
        # 主布局
        self._main_layout = QVBoxLayout(self._central_widget)
        
        # 分割器布局
        self._splitter = QSplitter()
        self._main_layout.addWidget(self._splitter)
        
        # 左侧面板 - 角色状态
        self._left_panel = QWidget()
        self._left_layout = QVBoxLayout(self._left_panel)
        self._splitter.addWidget(self._left_panel)
        
        # 中间面板 - 主输出
        self._center_panel = QWidget()
        self._center_layout = QVBoxLayout(self._center_panel)
        self._splitter.addWidget(self._center_panel)
        
        # 右侧面板 - 地图/任务
        self._right_panel = QWidget()
        self._right_layout = QVBoxLayout(self._right_panel)
        self._splitter.addWidget(self._right_panel)
        
        # 设置分割比例
        self._splitter.setSizes([250, 700, 250])
    
    def _connect_signals(self) -> None:
        """连接信号与槽."""
        # 连接引擎事件到GUI信号
        if self.engine:
            self.signals.game_started.connect(self._on_game_started)
            self.signals.game_stopped.connect(self._on_game_stopped)
    
    def _on_game_started(self) -> None:
        """游戏启动回调."""
        pass
    
    def _on_game_stopped(self) -> None:
        """游戏停止回调."""
        pass
    
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
    
    def closeEvent(self, event) -> None:
        """窗口关闭事件.
        
        Args:
            event: 关闭事件
        """
        # 通知引擎关闭
        if self.engine and self.engine.running:
            # 异步停止引擎
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.engine.stop())
            except RuntimeError:
                pass
        
        event.accept()


class GUIManager:
    """GUI管理器.
    
    管理GUI生命周期和与引擎的交互.
    """
    
    def __init__(self) -> None:
        """初始化GUI管理器."""
        self._main_window: Optional[MainWindow] = None
        self._engine: Optional["GameEngine"] = None
    
    def create_main_window(self, engine: Optional["GameEngine"] = None) -> MainWindow:
        """创建主窗口.
        
        Args:
            engine: 游戏引擎实例
            
        Returns:
            主窗口实例
        """
        self._engine = engine
        self._main_window = MainWindow(engine)
        return self._main_window
    
    @property
    def main_window(self) -> Optional[MainWindow]:
        """获取主窗口."""
        return self._main_window
    
    def update_from_character(self, character) -> None:
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
                character.location.key,
                character.location.description
            )

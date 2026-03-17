> 状态说明：
> - 对应阶段：阶段四（当前进行中）。
> - 当前已落地 GUI 入口为 `src/gui/main_window.py`。
> - 文中 `async_bridge.py`、`panels/*.py`、`themes/manager.py` 等路径是规划期拆分目标；若文件尚不存在，先确认是否真的需要新建。

## 快速定位

- 总体入口：看“主窗口架构”
- Qt/asyncio 桥接：看“qasync 桥接”
- 视图拆分：看“核心面板”及其子节
- 主题：看“主题系统”
- 当前真实入口优先以 `src/gui/main_window.py` 为准，规划路径只在需要拆分时参考

# GUI 系统

## 概述

使用 PySide6 构建现代化图形界面，通过 qasync 桥接 asyncio 和 Qt 事件循环。

## 主窗口架构

```python
# src/gui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, 
    QVBoxLayout, QHBoxLayout, QStatusBar
)
from PySide6.QtCore import Signal, QObject, Qt
import qasync

from ..engine.core.engine import GameEngine


class GameState(QObject):
    """游戏状态信号中心
    
    集中管理所有游戏状态变化信号，用于UI更新
    """
    
    # 角色状态
    player_hp_changed = Signal(int, int)      # 当前, 最大
    player_mp_changed = Signal(int, int)
    player_exp_changed = Signal(int, int)
    player_level_changed = int
    
    # 位置变化
    player_moved = Signal(object)  # Room对象
    
    # 战斗
    combat_started = Signal(object)
    combat_ended = Signal(object)
    combat_round = Signal(int)
    combat_log = Signal(str)  # 战斗日志
    
    # 物品
    inventory_changed = Signal()
    equipment_changed = Signal()
    
    # 任务
    quest_updated = Signal(str)   # quest_key
    quest_completed = Signal(str)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine
        self.game_state = GameState()
        
        self.setWindowTitle("金庸武侠MUD")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._connect_signals()
        self._setup_styles()
    
    def _setup_ui(self):
        """初始化UI组件"""
        # 中央分割器
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板（角色状态、罗盘）
        self.left_panel = LeftPanel(self.game_state)
        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(300)
        
        # 中央主视窗（场景、事件流、命令输入）
        self.main_view = MainViewPanel(self.engine, self.game_state)
        
        # 右侧面板（背包、武学、任务）
        self.right_panel = RightPanel(self.game_state)
        self.right_panel.setMinimumWidth(200)
        self.right_panel.setMaximumWidth(350)
        
        # 添加到分割器
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.main_view)
        self.main_splitter.addWidget(self.right_panel)
        
        # 设置比例
        self.main_splitter.setSizes([250, 700, 250])
        
        self.setCentralWidget(self.main_splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _connect_signals(self):
        """连接引擎事件到GUI信号"""
        # TODO: 连接引擎回调
        pass
    
    def _setup_styles(self):
        """设置样式"""
        # 加载主题
        theme_manager = ThemeManager()
        qss = theme_manager.load_theme("ink")
        self.setStyleSheet(qss)
    
    def closeEvent(self, event):
        """关闭时保存并停止引擎"""
        # 自动存档
        asyncio.create_task(self._auto_save_and_exit())
        event.accept()
    
    async def _auto_save_and_exit(self):
        """自动存档并退出"""
        self.status_bar.showMessage("正在保存...")
        await self.engine.save.auto_save()
        await self.engine.stop()


class LeftPanel(QWidget):
    """左侧面板 - 角色状态、罗盘"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 角色状态面板
        self.status_panel = StatusPanel(self.game_state)
        layout.addWidget(self.status_panel)
        
        # 罗盘
        self.compass = CompassWidget(self.game_state)
        layout.addWidget(self.compass)
        
        layout.addStretch()


class RightPanel(QWidget):
    """右侧面板 - 背包、武学、任务"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
    
    def _setup_ui(self):
        from PySide6.QtWidgets import QTabWidget
        
        layout = QVBoxLayout(self)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 背包
        self.inventory_panel = InventoryPanel(self.game_state)
        self.tabs.addTab(self.inventory_panel, "背包")
        
        # 装备
        self.equipment_panel = EquipmentPanel(self.game_state)
        self.tabs.addTab(self.equipment_panel, "装备")
        
        # 武学
        self.wuxue_panel = WuxuePanel(self.game_state)
        self.tabs.addTab(self.wuxue_panel, "武学")
        
        # 任务
        self.quest_panel = QuestPanel(self.game_state)
        self.tabs.addTab(self.quest_panel, "任务")
        
        layout.addWidget(self.tabs)
```

## qasync 桥接

```python
# src/gui/async_bridge.py
import asyncio
from qasync import QEventLoop
from PySide6.QtCore import QCoreApplication


class AsyncBridge:
    """asyncio与PySide6桥接
    
    使用qasync库将asyncio事件循环与Qt事件循环集成
    """
    
    def __init__(self, app: QCoreApplication):
        self.app = app
        self.loop = QEventLoop(app)
        asyncio.set_event_loop(self.loop)
    
    def run(self, coro):
        """运行协程"""
        return self.loop.run_until_complete(coro)
    
    def create_task(self, coro):
        """创建任务"""
        return self.loop.create_task(coro)
    
    def run_forever(self):
        """运行事件循环"""
        self.loop.run_forever()


# 使用示例
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    bridge = AsyncBridge(app)
    
    # 启动引擎
    async def main():
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        # 创建主窗口
        window = MainWindow(engine)
        window.show()
    
    bridge.run(main())
    bridge.run_forever()
```

## 核心面板

### 主视窗面板

```python
# src/gui/panels/main_view.py
from PySide6.QtWidgets import (
    QTextBrowser, QLineEdit, QVBoxLayout, 
    QWidget, QSplitter
)
from PySide6.QtCore import Qt, QUrl


class MainViewPanel(QWidget):
    """主视窗 - 场景描述、事件流、命令输入"""
    
    def __init__(self, engine: GameEngine, game_state: GameState):
        super().__init__()
        self.engine = engine
        self.game_state = game_state
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 场景描述区
        self.scene_view = QTextBrowser()
        self.scene_view.setOpenLinks(False)
        self.scene_view.anchorClicked.connect(self._on_link_clicked)
        self.scene_view.setMinimumHeight(200)
        
        # 事件流
        self.event_log = QTextBrowser()
        self.event_log.setMaximumBlockCount(100)  # 限制行数
        self.event_log.setMinimumHeight(150)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.scene_view)
        splitter.addWidget(self.event_log)
        splitter.setSizes([300, 200])
        
        # 命令输入
        self.cmd_input = CommandLineEdit()
        self.cmd_input.returnPressed.connect(self._on_command)
        self.cmd_input.setPlaceholderText("输入命令...")
        
        layout.addWidget(splitter)
        layout.addWidget(self.cmd_input)
    
    def update_scene(self, room):
        """更新场景显示"""
        html = self._render_room_html(room)
        self.scene_view.setHtml(html)
    
    def append_event(self, text: str, style: str = "normal"):
        """添加事件到流"""
        colors = {
            "normal": "#000000",
            "combat": "#cc0000",
            "chat": "#0066cc",
            "system": "#666666",
        }
        color = colors.get(style, "#000000")
        formatted = f'<span style="color: {color};">{text}</span>'
        self.event_log.append(formatted)
    
    def _on_command(self):
        """执行命令"""
        text = self.cmd_input.text().strip()
        if not text:
            return
        
        self.cmd_input.clear()
        self.cmd_input.addToHistory(text)
        
        # 发送到引擎
        asyncio.create_task(self._send_command(text))
    
    async def _send_command(self, text: str):
        """发送命令到引擎"""
        # TODO: 获取当前玩家ID
        player_id = 1
        result = await self.engine.process_input(player_id, text)
        self.append_event(result.message)
    
    def _render_room_html(self, room) -> str:
        """渲染房间为富文本"""
        exits = room.get_exits()
        exit_links = ' '.join(
            f'<a href="go {ex.direction}">[{ex.direction_name}]</a>'
            for ex in exits
        )
        
        return f"""
        <h2>{room.key}</h2>
        <p>{room.description}</p>
        <p><b>出口:</b> {exit_links}</p>
        """
    
    def _on_link_clicked(self, url: QUrl):
        """处理链接点击"""
        cmd = url.toString()
        self.cmd_input.setText(cmd)
        self._on_command()


class CommandLineEdit(QLineEdit):
    """支持历史记录和自动补全的命令输入"""
    
    def __init__(self):
        super().__init__()
        self.history: list[str] = []
        self.history_idx = 0
    
    def addToHistory(self, text: str):
        """添加到历史"""
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self.history_idx = len(self.history)
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Up:
            # 上一条历史
            if self.history_idx > 0:
                self.history_idx -= 1
                self.setText(self.history[self.history_idx])
        
        elif event.key() == Qt.Key_Down:
            # 下一条历史
            if self.history_idx < len(self.history) - 1:
                self.history_idx += 1
                self.setText(self.history[self.history_idx])
            else:
                self.history_idx = len(self.history)
                self.clear()
        
        elif event.key() == Qt.Key_Tab:
            # 自动补全
            # TODO: 实现命令补全
            pass
        
        else:
            super().keyPressEvent(event)
```

### 角色状态面板

```python
# src/gui/panels/status.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel, QGridLayout
)
from PySide6.QtCore import Slot


class StatusPanel(QWidget):
    """角色状态面板 - 气血/内力/精力"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("角色状态")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 气血
        self.hp_bar = self._create_bar("气血", "#c0392b", "#e74c3c")
        layout.addLayout(self.hp_bar["layout"])
        
        # 内力
        self.mp_bar = self._create_bar("内力", "#8e44ad", "#9b59b6")
        layout.addLayout(self.mp_bar["layout"])
        
        # 精力
        self.ep_bar = self._create_bar("精力", "#27ae60", "#2ecc71")
        layout.addLayout(self.ep_bar["layout"])
        
        # 等级经验
        self.level_label = QLabel("等级: 1")
        self.exp_bar = QProgressBar()
        self.exp_bar.setMaximum(100)
        self.exp_bar.setValue(0)
        layout.addWidget(self.level_label)
        layout.addWidget(self.exp_bar)
        
        layout.addStretch()
    
    def _create_bar(self, name: str, bg_color: str, fg_color: str) -> dict:
        """创建进度条"""
        layout = QGridLayout()
        
        label = QLabel(name)
        bar = QProgressBar()
        bar.setTextVisible(True)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {bg_color};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {fg_color};
            }}
        """)
        
        layout.addWidget(label, 0, 0)
        layout.addWidget(bar, 0, 1)
        
        return {"layout": layout, "bar": bar}
    
    def _connect_signals(self):
        """连接信号"""
        self.game_state.player_hp_changed.connect(self._update_hp)
        self.game_state.player_mp_changed.connect(self._update_mp)
    
    @Slot(int, int)
    def _update_hp(self, current: int, max_hp: int):
        """更新气血"""
        bar = self.hp_bar["bar"]
        bar.setMaximum(max_hp)
        bar.setValue(current)
        bar.setFormat(f"%v / %m ({current/max_hp*100:.0f}%)")
        
        # 低血量警告
        if current / max_hp < 0.2:
            bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #e74c3c; }
            """)
    
    @Slot(int, int)
    def _update_mp(self, current: int, max_mp: int):
        """更新内力"""
        bar = self.mp_bar["bar"]
        bar.setMaximum(max_mp)
        bar.setValue(current)
        bar.setFormat(f"%v / %m ({current/max_mp*100:.0f}%)")
```

### 罗盘控件

```python
# src/gui/panels/compass.py
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton
from PySide6.QtCore import Qt


class CompassWidget(QWidget):
    """八方向罗盘"""
    
    DIRECTIONS = {
        "nw": (0, 0), "n": (0, 1), "ne": (0, 2),
        "w":  (1, 0), "look": (1, 1), "e": (1, 2),
        "sw": (2, 0), "s": (2, 1), "se": (2, 2),
    }
    
    DIRECTION_NAMES = {
        "nw": "西北", "n": "北", "ne": "东北",
        "w": "西", "look": "环顾", "e": "东",
        "sw": "西南", "s": "南", "se": "东南",
    }
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(4)
        
        for dir_key, (row, col) in self.DIRECTIONS.items():
            btn = QPushButton(self.DIRECTION_NAMES[dir_key])
            btn.setFixedSize(50, 40)
            btn.setEnabled(False)  # 默认禁用
            btn.clicked.connect(lambda d=dir_key: self._on_direction(d))
            
            self._buttons[dir_key] = btn
            layout.addWidget(btn, row, col)
        
        # 上下按钮
        self.btn_up = QPushButton("上")
        self.btn_up.setEnabled(False)
        self.btn_up.clicked.connect(lambda: self._on_direction("up"))
        layout.addWidget(self.btn_up, 0, 3)
        
        self.btn_down = QPushButton("下")
        self.btn_down.setEnabled(False)
        self.btn_down.clicked.connect(lambda: self._on_direction("down"))
        layout.addWidget(self.btn_down, 2, 3)
    
    def update_available_exits(self, room):
        """根据当前房间更新可用出口"""
        exits = {ex.direction for ex in room.get_exits()}
        
        for dir_key, btn in self._buttons.items():
            if dir_key == "look":
                btn.setEnabled(True)
            else:
                btn.setEnabled(dir_key in exits)
        
        self.btn_up.setEnabled("up" in exits)
        self.btn_down.setEnabled("down" in exits)
    
    def _on_direction(self, direction: str):
        """方向按钮点击"""
        if direction == "look":
            cmd = "look"
        else:
            cmd = f"go {direction}"
        
        # 发送命令信号
        # TODO: 通过信号发送
        print(f"执行命令: {cmd}")
```

## 主题系统

```python
# src/gui/themes/manager.py
from pathlib import Path


class ThemeManager:
    """主题管理器"""
    
    THEMES = {
        "ink": "水墨",      # 默认
        "metal": "金属",
        "classic": "经典",
        "dark": "夜间"
    }
    
    def __init__(self):
        self.current_theme = "ink"
    
    def load_theme(self, theme_name: str) -> str:
        """加载QSS样式"""
        qss_path = Path(f"resources/themes/{theme_name}.qss")
        if qss_path.exists():
            return qss_path.read_text(encoding="utf-8")
        return self._get_default_theme()
    
    def apply_theme(self, app, theme_name: str):
        """应用主题"""
        qss = self.load_theme(theme_name)
        app.setStyleSheet(qss)
        self.current_theme = theme_name
    
    def _get_default_theme(self) -> str:
        """默认主题"""
        return """
        QMainWindow {
            background-color: #f5f5f0;
        }
        QTextBrowser {
            background-color: #fafaf5;
            color: #2c2c2c;
            border: 1px solid #d0d0c8;
            font-family: "Noto Serif CJK SC", "SimSun", serif;
            font-size: 14px;
        }
        QPushButton {
            background-color: #e8e4dc;
            border: 1px solid #8b4513;
            padding: 5px 15px;
            border-radius: 3px;
        }
        """
```


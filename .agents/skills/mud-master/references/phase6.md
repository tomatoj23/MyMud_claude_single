# 阶段六：存档与系统功能（第16-17周）

## 阶段目标

实现完善的存档系统和后台管理功能。

## 模块清单

| 顺序 | 模块 | 依赖 | 状态 |
|:---|:---|:---|:---|
| 1 | 存档系统 | 所有阶段完成 | 待开始 |
| 2 | 后台管理系统 | 存档系统 | 待开始 |

## 6.1 存档系统（第16周）

### 存档管理器

**功能需求：**
- MessagePack序列化
- 存档压缩与加密
- 自动存档触发（关键节点）
- 存档兼容性检查

**核心接口设计：**

```python
# src/engine/save/manager.py
import msgpack
import gzip
from pathlib import Path
from datetime import datetime
from typing import Optional


class SaveInfo:
    """存档信息"""
    slot: str
    name: str
    timestamp: datetime
    version: str
    play_time: int  # 秒
    level: int
    location: str


class SaveManager:
    """存档管理器"""
    
    SAVE_DIR = Path("saves")
    AUTO_SAVE_SLOTS = 10
    QUICK_SAVE_SLOT = "quick"
    
    def __init__(self, engine: "GameEngine"):
        self.engine = engine
    
    async def save(
        self, 
        slot: str, 
        name: str = "", 
        screenshot: Optional[bytes] = None
    ) -> Path:
        """
        保存游戏
        序列化内容：
        - 玩家角色完整状态
        - 世界状态
        - 任务进度
        - 时间戳和元数据
        """
    
    async def load(self, slot: str) -> bool:
        """加载存档"""
    
    async def auto_save(self) -> Path:
        """自动存档（轮转）"""
    
    def get_save_list(self) -> list[SaveInfo]:
        """获取所有存档信息"""
    
    def delete_save(self, slot: str) -> bool:
        """删除存档"""
    
    def _serialize(self) -> bytes:
        """序列化游戏状态"""
        data = {
            "version": "GAME_VERSION",
            "timestamp": datetime.now().isoformat(),
            "player": self._serialize_character(),
            "world_state": self._serialize_world(),
            "quests": self._serialize_quests(),
        }
        return msgpack.packb(data, use_bin_type=True)
```

**自动存档触发点：**
- 进入新区域
- 完成任务
- 战斗胜利
- 重要剧情节点
- 手动存档
- 退出游戏

**存档文件结构：**
```
saves/
├── quick.save          # 快速存档
├── auto_01.save        # 自动存档1-10（轮转）
├── auto_02.save
├── ...
├── auto_10.save
├── slot_01.save        # 手动存档槽位
├── slot_02.save
└── meta.json           # 存档元数据索引
```

### 版本兼容性

```python
# src/engine/save/version.py
SAVE_VERSION = 1  # 当前存档格式版本

class SaveCompatibility:
    """存档兼容性处理"""
    
    @staticmethod
    def check_version(data: dict) -> tuple[bool, str]:
        """
        检查存档版本兼容性
        返回: (是否兼容, 错误信息)
        """
        version = data.get("version", 0)
        if version > SAVE_VERSION:
            return False, f"存档版本(v{version})高于游戏版本(v{SAVE_VERSION})"
        if version < SAVE_VERSION:
            # 尝试迁移
            return SaveCompatibility.migrate(data, version)
        return True, ""
    
    @staticmethod
    def migrate(data: dict, from_version: int) -> tuple[bool, str]:
        """迁移旧版本存档"""
        # 版本迁移逻辑
        migrations = {
            0: SaveCompatibility._migrate_v0_to_v1,
        }
        
        for v in range(from_version, SAVE_VERSION):
            if v in migrations:
                data = migrations[v](data)
        
        return True, ""
```

## 6.2 后台管理系统（第17周）

### 开发者模式（F12）

```python
# src/gui/dev/manager.py
from PySide6.QtWidgets import QTabWidget, QWidget


class DeveloperMode(QWidget):
    """开发者模式面板"""
    
    def __init__(self, engine: "GameEngine"):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("开发者模式")
        self._setup_panels()
    
    def _setup_panels(self):
        self.tabs = QTabWidget()
        
        # 对象浏览器
        self.obj_browser = ObjectBrowser(self.engine)
        self.tabs.addTab(self.obj_browser, "对象")
        
        # 日志查看器
        self.log_viewer = LogViewer()
        self.tabs.addTab(self.log_viewer, "日志")
        
        # 性能监控
        self.perf_monitor = PerformanceMonitor()
        self.tabs.addTab(self.perf_monitor, "性能")
        
        # 平衡性测试
        self.balance_tester = BalanceTester(self.engine)
        self.tabs.addTab(self.balance_tester, "平衡测试")
        
        # 命令控制台
        self.console = DevConsole(self.engine)
        self.tabs.addTab(self.console, "控制台")
```

### 对象浏览器

```python
# src/gui/dev/object_browser.py
class ObjectBrowser(QWidget):
    """游戏对象浏览器"""
    
    def __init__(self, engine: "GameEngine"):
        super().__init__()
        self.engine = engine
        self._setup_ui()
    
    def _setup_ui(self):
        # 对象树
        self.obj_tree = QTreeWidget()
        self.obj_tree.setHeaderLabels(["ID", "Key", "Type", "Location"])
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索对象...")
        
        # 属性编辑器
        self.prop_editor = PropertyEditor()
        
        # 操作按钮
        self.btn_refresh = QPushButton("刷新")
        self.btn_delete = QPushButton("删除")
        self.btn_teleport = QPushButton("传送玩家到此处")
    
    def refresh_objects(self):
        """刷新对象列表"""
        # 从ObjectManager获取所有对象
        pass
    
    def edit_object(self, obj_id: int):
        """编辑对象属性"""
        pass
```

### 平衡性测试台

```python
# src/gui/dev/balance.py
from dataclasses import dataclass


@dataclass
class CombatStats:
    """战斗统计数据"""
    total_battles: int
    wins_a: int
    wins_b: int
    draws: int
    avg_rounds: float
    damage_dist: list[int]  # 伤害分布


class BalanceTester(QWidget):
    """平衡性测试工具"""
    
    def __init__(self, engine: "GameEngine"):
        super().__init__()
        self.engine = engine
        self._setup_ui()
    
    def _setup_ui(self):
        # 角色A配置
        self.char_a_config = CharacterConfigWidget("角色A")
        
        # 角色B配置
        self.char_b_config = CharacterConfigWidget("角色B")
        
        # 测试参数
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(10, 10000)
        self.rounds_spin.setValue(1000)
        
        # 运行按钮
        self.btn_run = QPushButton("开始模拟")
        self.btn_run.clicked.connect(self.run_simulation)
        
        # 结果展示
        self.result_text = QTextBrowser()
    
    async def run_combat_simulation(
        self,
        char_a_template: dict,
        char_b_template: dict,
        rounds: int = 1000
    ) -> CombatStats:
        """
        批量战斗模拟
        统计：胜率、平均回合数、伤害分布
        """
        wins_a = wins_b = draws = 0
        total_rounds = 0
        
        for _ in range(rounds):
            # 创建模拟角色
            char_a = self._create_mock_character(char_a_template)
            char_b = self._create_mock_character(char_b_template)
            
            # 执行战斗
            result = await self._simulate_combat(char_a, char_b)
            
            if result.winner == char_a:
                wins_a += 1
            elif result.winner == char_b:
                wins_b += 1
            else:
                draws += 1
            
            total_rounds += result.rounds
        
        return CombatStats(
            total_battles=rounds,
            wins_a=wins_a,
            wins_b=wins_b,
            draws=draws,
            avg_rounds=total_rounds / rounds,
            damage_dist=[]
        )
    
    def generate_report(self, stats: CombatStats) -> str:
        """生成平衡性报告"""
        report = f"""
战斗模拟报告
=============
模拟场次: {stats.total_battles}
角色A胜率: {stats.wins_a / stats.total_battles * 100:.1f}%
角色B胜率: {stats.wins_b / stats.total_battles * 100:.1f}%
平局率: {stats.draws / stats.total_battles * 100:.1f}%
平均回合: {stats.avg_rounds:.1f}

平衡性评估:
{'-' * 40}
"""
        # 评估平衡性
        win_rate_a = stats.wins_a / stats.total_battles
        if 0.45 <= win_rate_a <= 0.55:
            report += "✓ 平衡性良好（胜率差 < 10%）\n"
        elif 0.35 <= win_rate_a <= 0.65:
            report += "⚠ 略有失衡（胜率差 10-30%）\n"
        else:
            report += "✗ 严重失衡（胜率差 > 30%）\n"
        
        return report
```

### 开发者命令控制台

```python
# src/gui/dev/console.py
class DevConsole(QWidget):
    """开发者命令控制台"""
    
    COMMON_COMMANDS = [
        ("god", "开启无敌模式"),
        ("levelup <n>", "提升n级"),
        ("learn <skill>", "学习武功"),
        ("goto <room_id>", "传送到房间"),
        ("spawn <obj_key>", "生成对象"),
        ("killall", "清除所有NPC"),
        ("resetcd", "重置所有冷却"),
        ("save", "强制存档"),
        ("load <slot>", "加载存档"),
    ]
    
    def __init__(self, engine: "GameEngine"):
        super().__init__()
        self.engine = engine
        self.history: list[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        # 命令历史
        self.output = QTextBrowser()
        
        # 命令输入
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.execute_command)
        
        # 常用命令按钮
        self.btn_panel = QWidget()
        self._create_quick_buttons()
    
    def execute_command(self):
        """执行开发者命令"""
        cmd = self.input.text().strip()
        self.history.append(cmd)
        
        parts = cmd.split()
        command = parts[0]
        args = parts[1:]
        
        handlers = {
            "god": self._cmd_god,
            "levelup": self._cmd_levelup,
            "learn": self._cmd_learn,
            "goto": self._cmd_goto,
            "spawn": self._cmd_spawn,
            "killall": self._cmd_killall,
            "resetcd": self._cmd_resetcd,
            "save": self._cmd_save,
            "load": self._cmd_load,
        }
        
        if command in handlers:
            try:
                result = handlers[command](*args)
                self.output.append(f"> {cmd}\n{result}")
            except Exception as e:
                self.output.append(f"> {cmd}\n错误: {e}")
        else:
            self.output.append(f"> {cmd}\n未知命令: {command}")
        
        self.input.clear()
```

## 阶段六验收标准

- [ ] 存档/读档功能完整
- [ ] 自动存档正常触发
- [ ] 存档版本兼容性处理正确
- [ ] 开发者模式可实时查看/修改数据
- [ ] 对象浏览器可查看和编辑游戏对象
- [ ] 战斗模拟器可批量测试并生成报告
- [ ] 命令控制台可执行开发者命令

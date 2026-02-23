# 消息总线系统

## 概述

消息总线（MessageBus）是引擎与GUI之间的消息传递中间层，解耦了游戏逻辑与界面显示。

## 核心组件

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Command   │────▶│ MessageBus  │────▶│  Console    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  GUI Panel  │     │  Log File   │     │   Debug     │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 消息类型

```python
from enum import Enum

class MessageType(Enum):
    SYSTEM = "system"           # 系统消息
    ERROR = "error"             # 错误消息
    WARNING = "warning"         # 警告消息
    INFO = "info"               # 信息消息
    DEBUG = "debug"             # 调试消息
    COMBAT = "combat"           # 战斗消息
    DIALOGUE = "dialogue"       # 对话消息
    NOTIFICATION = "notify"     # 通知消息
    STATUS = "status"           # 状态更新
    PROMPT = "prompt"           # 输入提示
```

## 基本使用

### 1. 发送消息

```python
from src.engine.core.messages import MessageBus, MessageType

# 获取全局消息总线
bus = get_message_bus()

# 发送文本消息
bus.emit_text(MessageType.COMBAT, "你对敌人造成了50点伤害！")

# 发送带数据的消息
bus.emit_text(
    MessageType.STATUS,
    "等级提升！",
    old_level=9,
    new_level=10
)
```

### 2. 在命令中使用

```python
from src.engine.commands.base import Command
from src.engine.core.messages import MessageType

class CmdAttack(Command):
    key = "attack"
    
    async def execute(self):
        target = self.parse_target()
        if not target:
            self.msg("你要攻击谁？", MessageType.ERROR)
            return
        
        damage = self.calculate_damage()
        target.hp -= damage
        
        # 发送不同类型的消息
        self.msg(f"你对{target.name}造成了{damage}点伤害！", MessageType.COMBAT)
        
        if target.hp <= 0:
            self.msg(f"{target.name}倒下了！", MessageType.SYSTEM)
```

### 3. 订阅消息（GUI中）

```python
from PySide6.QtCore import QObject, Signal

class GameController(QObject):
    # 定义信号
    message_received = Signal(str, str, dict)  # type, content, data
    status_updated = Signal(str, dict)         # status_type, data
    
    def __init__(self):
        super().__init__()
        self._setup_message_bus()
    
    def _setup_message_bus(self):
        bus = get_message_bus()
        
        # 订阅所有文本消息
        bus.subscribe(self._on_message)
        
        # 订阅特定状态更新
        bus.subscribe_status("player_hp", self._on_hp_changed)
        bus.subscribe_status("inventory", self._on_inventory_changed)
    
    def _on_message(self, msg: Message):
        """处理消息"""
        # 发送到GUI显示
        self.message_received.emit(
            msg.msg_type.value,
            msg.content,
            msg.data
        )
        
        # 根据类型处理
        if msg.msg_type == MessageType.COMBAT:
            self._show_combat_animation(msg)
        elif msg.msg_type == MessageType.ERROR:
            self._show_error_popup(msg)
    
    def _on_hp_changed(self, data: dict):
        """处理血量变化"""
        current = data.get("current", 0)
        maximum = data.get("max", 100)
        self.status_updated.emit("hp", {"current": current, "max": maximum})
```

## 与GameEngine集成

```python
from src.engine.core.engine import GameEngine
from src.engine.core.messages import MessageBus

# 创建时传入消息总线
bus = MessageBus()
engine = GameEngine(config, message_bus=bus)

# 或在创建后设置
engine.message_bus.subscribe(my_handler)
```

## 消息处理器基类

```python
from src.engine.core.messages import MessageHandler, MessageType

class Character(MessageHandler):
    """角色类继承MessageHandler，获得消息发送能力"""
    
    def take_damage(self, damage: int):
        self.hp -= damage
        
        # 使用继承的msg方法
        self.msg(f"你受到了{damage}点伤害！", MessageType.COMBAT)
        
        if self.hp <= 0:
            self.msg("你倒下了...", MessageType.ERROR)
            self.die()
```

## 高级用法

### 1. 历史消息

```python
# 获取最近100条消息
history = bus.get_history(limit=100)

# 获取特定类型的消息
combat_logs = bus.get_history(
    msg_type=MessageType.COMBAT,
    limit=50
)
```

### 2. 消息过滤

```python
# 只接收战斗消息
def combat_only_handler(msg: Message):
    if msg.msg_type != MessageType.COMBAT:
        return
    process_combat_message(msg)

bus.subscribe(combat_only_handler)
```

### 3. 状态更新

```python
# 发送状态更新（用于实时UI刷新）
char.emit_status("player_stats", {
    "hp": char.hp,
    "mp": char.mp,
    "level": char.level,
})
```

## GUI集成最佳实践

### 1. 消息显示面板

```python
class MessagePanel(QTextBrowser):
    """消息显示面板"""
    
    def __init__(self):
        super().__init__()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置消息样式"""
        self.styles = {
            MessageType.SYSTEM: "color: #333;",
            MessageType.ERROR: "color: #c0392b; font-weight: bold;",
            MessageType.WARNING: "color: #f39c12;",
            MessageType.COMBAT: "color: #8e44ad;",
            MessageType.DIALOGUE: "color: #27ae60; font-style: italic;",
        }
    
    def append_message(self, msg_type: str, content: str, data: dict):
        """添加消息到面板"""
        style = self.styles.get(MessageType(msg_type), "")
        html = f'<span style="{style}">{content}</span>'
        self.append(html)
```

### 2. 信号桥接

```python
class MessageBridge(QObject):
    """消息总线与Qt信号的桥接"""
    
    text_output = Signal(str, str, dict)      # type, content, data
    status_update = Signal(str, dict)         # status_type, data
    command_executed = Signal(str, bool, str) # cmd, success, result
    
    def __init__(self, bus: MessageBus):
        super().__init__()
        self.bus = bus
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        self.bus.subscribe(self._on_message)
    
    def _on_message(self, msg: Message):
        self.text_output.emit(
            msg.msg_type.value,
            msg.content,
            msg.data
        )
```

## 注意事项

1. **线程安全** - MessageBus 不是线程安全的，所有操作应在同一线程
2. **内存管理** - 历史消息有上限，防止内存泄漏
3. **异常处理** - 消息处理器异常不应影响其他处理器
4. **性能考虑** - 大量消息时考虑批量处理或节流

## 迁移指南

从直接调用迁移到消息总线：

```python
# 旧代码
class Command:
    def msg(self, text: str, **kwargs):
        if self.caller:
            self.caller.msg(text, **kwargs)

# 新代码
class Command(MessageHandler):
    def msg(self, text: str, msg_type=MessageType.SYSTEM, **kwargs):
        if hasattr(self.caller, 'message_bus') and self.caller.message_bus:
            self.caller.message_bus.emit_text(msg_type, text, **kwargs)
        elif hasattr(self.caller, 'msg'):
            self.caller.msg(text, **kwargs)
        else:
            get_message_bus().emit_text(msg_type, text, **kwargs)
```

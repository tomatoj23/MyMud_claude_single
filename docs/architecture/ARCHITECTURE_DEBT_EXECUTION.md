# 架构债务清偿执行手册

> 每个债务的详细执行步骤和代码模板

---

## ARCH-001: 单例模式状态污染

### 执行步骤

#### Step 1: 修改 ConfigManager (30分钟)

**文件**: `src/utils/config.py`

**修改内容**:
```python
class ConfigManager:
    _instance: ConfigManager | None = None
    _lock = threading.Lock()
    
    @classmethod
    def reset(cls) -> None:
        """重置单例实例（仅用于测试）.
        
        警告: 不要在生产代码中调用此方法！
        """
        with cls._lock:
            cls._instance = None
    
    @classmethod
    def get_instance(cls) -> ConfigManager:
        """获取单例实例（线程安全）."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
```

#### Step 2: 创建测试隔离fixture (20分钟)

**文件**: `tests/conftest.py`

**新增**:
```python
import pytest
from src.utils.config import ConfigManager

@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试前重置所有单例状态."""
    ConfigManager.reset()
    yield
    ConfigManager.reset()
```

#### Step 3: 验证测试 (10分钟)

```bash
python -m pytest tests/unit/test_config.py::test_detect_environment_frozen -v --count=10
```

---

## ARCH-002: 异步代码同步调用风险

### 执行步骤

#### Step 1: 修改 Message 类 (15分钟)

**文件**: `src/engine/core/messages.py`

**修改前**:
```python
self.timestamp = asyncio.get_event_loop().time()
```

**修改后**:
```python
import time

class Message:
    def __init__(self, ...):
        # 使用标准时间戳，不依赖事件循环
        self.timestamp = time.time()
        self.timestamp_ns = time.time_ns()
```

#### Step 2: 添加兼容性处理 (可选)

```python
import time
import asyncio

class Message:
    def __init__(self, ...):
        # 优先使用asyncio时间（高精度）
        try:
            loop = asyncio.get_running_loop()
            self.timestamp = loop.time()
        except RuntimeError:
            # 不在事件循环中，使用标准时间
            self.timestamp = time.time()
```

#### Step 3: 验证测试 (10分钟)

```bash
python -m pytest tests/unit/test_messages.py::test_msg_no_caller -v --count=10
```

---

## ARCH-004: 测试覆盖率提升

### Item模块补充测试

**文件**: `tests/unit/test_item_coverage.py`

```python
"""Item模块覆盖率补充测试."""

import pytest
from src.game.typeclasses.item import Item

class TestItemCanPickupDetailed:
    """详细测试can_pickup方法."""
    
    def test_can_pickup_with_no_weight_attribute(self, mock_manager):
        """测试物品无weight属性时默认可拾取."""
        # 实现测试...
        pass
    
    def test_can_pickup_with_negative_weight(self, mock_manager):
        """测试负重量处理."""
        pass
    
    def test_can_pickup_zero_weight(self, mock_manager):
        """测试零重量物品."""
        pass

class TestItemCanUseDetailed:
    """详细测试can_use方法."""
    
    def test_can_use_consumable(self, mock_manager):
        """测试消耗品使用条件."""
        pass
    
    def test_can_use_equipment(self, mock_manager):
        """测试装备使用条件."""
        pass

class TestItemOnUseDetailed:
    """详细测试on_use方法."""
    
    @pytest.mark.asyncio
    async def test_on_use_healing_item(self, mock_manager):
        """测试治疗物品使用效果."""
        pass
    
    @pytest.mark.asyncio
    async def test_on_use_buff_item(self, mock_manager):
        """测试BUFF物品使用效果."""
        pass
```

### Room模块补充测试

**文件**: `tests/unit/test_room_coverage.py`

```python
"""Room模块覆盖率补充测试."""

import pytest

class TestRoomGetContentsAsync:
    """测试异步获取内容."""
    
    @pytest.mark.asyncio
    async def test_get_contents_async_empty(self, mock_manager):
        """测试空房间异步获取."""
        pass
    
    @pytest.mark.asyncio
    async def test_get_contents_async_with_items(self, mock_manager):
        """测试有物品时异步获取."""
        pass

class TestRoomAtDescDetailed:
    """详细测试房间描述."""
    
    def test_at_desc_with_exits(self, mock_manager):
        """测试描述包含出口."""
        pass
    
    def test_at_desc_with_items(self, mock_manager):
        """测试描述包含物品."""
        pass
    
    def test_at_desc_with_characters(self, mock_manager):
        """测试描述包含其他角色."""
        pass
```

---

## ARCH-005: 魔法字符串 → 枚举

### 创建枚举模块

**文件**: `src/game/types/enums.py`

```python
"""游戏系统枚举定义."""

from enum import Enum, auto

class MoveType(str, Enum):
    """招式类型."""
    ATTACK = "attack"
    DEFEND = "defend"
    CAST = "cast"
    USE_ITEM = "item"
    FLEE = "flee"
    SPECIAL = "special"

class BuffType(str, Enum):
    """BUFF/DEBUFF类型."""
    POISON = "poison"
    STUN = "stun"
    SILENCE = "silence"
    BUFF = "buff"
    DEBUFF = "debuff"
    HEAL_OVER_TIME = "hot"
    DAMAGE_OVER_TIME = "dot"

class DamageType(str, Enum):
    """伤害类型."""
    PHYSICAL = "physical"
    INTERNAL = "internal"  # 内功伤害
    POISON = "poison"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"

class EquipmentSlot(str, Enum):
    """装备槽位（替代原有字符串）."""
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    HEAD = "head"
    BODY = "body"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    NECK = "neck"
    RING1 = "ring1"
    RING2 = "ring2"

class NPCState(str, Enum):
    """NPC状态."""
    IDLE = "idle"
    PATROL = "patrol"
    COMBAT = "combat"
    DEAD = "dead"
    FLEE = "flee"

class QuestStatus(str, Enum):
    """任务状态."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TURNED_IN = "turned_in"
```

### 批量替换脚本

**工具**: `tools/migrate_magic_strings.py`

```python
#!/usr/bin/env python3
"""魔法字符串迁移脚本."""

import re
from pathlib import Path

REPLACEMENTS = {
    # 招式类型
    r'["\']attack["\']': 'MoveType.ATTACK',
    r'["\']defend["\']': 'MoveType.DEFEND',
    r'["\']cast["\']': 'MoveType.CAST',
    
    # BUFF类型
    r'["\']poison["\']': 'BuffType.POISON',
    r'["\']stun["\']': 'BuffType.STUN',
    
    # 伤害类型
    r'["\']physical["\']': 'DamageType.PHYSICAL',
    r'["\']internal["\']': 'DamageType.INTERNAL',
}

def migrate_file(filepath: Path) -> str:
    """迁移单个文件."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return f"已更新: {filepath}"
    return f"未变更: {filepath}"

if __name__ == "__main__":
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        print(migrate_file(py_file))
```

---

## ARCH-006: 循环导入风险

### 创建协议接口

**文件**: `src/game/interfaces.py`

```python
"""游戏对象协议接口.

定义核心抽象，避免循环导入.
"""

from typing import Protocol, runtime_checkable
from enum import Enum

class Position(Protocol):
    """位置协议."""
    x: int
    y: int
    z: int

@runtime_checkable
class Combatant(Protocol):
    """战斗参与者协议."""
    
    @property
    def name(self) -> str: ...
    
    @property
    def hp(self) -> tuple[int, int]: ...
    
    @property
    def mp(self) -> tuple[int, int]: ...
    
    def modify_hp(self, delta: int) -> int: ...
    
    def modify_mp(self, delta: int) -> int: ...
    
    def get_attack(self) -> int: ...
    
    def get_defense(self) -> int: ...

@runtime_checkable
class ItemHolder(Protocol):
    """物品持有者协议."""
    
    def get_current_weight(self) -> int: ...
    
    def get_max_weight(self) -> int: ...
    
    def can_carry(self, item) -> tuple[bool, str]: ...

@runtime_checkable
class Movable(Protocol):
    """可移动对象协议."""
    
    async def move_to(self, destination) -> bool: ...
    
    @property
    def location(self): ...
```

### 应用协议

**文件**: `src/game/combat/core.py`

```python
# 替换前
if TYPE_CHECKING:
    from src.game.typeclasses.character import Character

async def process_turn(self, character: "Character"):
    ...

# 替换后
from src.game.interfaces import Combatant

async def process_turn(self, character: Combatant):
    ...
```

---

## ARCH-007: 异常处理完善

### 定义异常层次

**文件**: `src/utils/exceptions.py`

```python
"""游戏异常定义."""

class GameException(Exception):
    """游戏基础异常."""
    
    def __init__(self, message: str, *, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}

class CombatException(GameException):
    """战斗相关异常."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="COMBAT_ERROR", **kwargs)

class InvalidTargetError(CombatException):
    """无效目标错误."""
    
    def __init__(self, target=None):
        self.target = target
        super().__init__(
            "无法攻击这个目标",
            code="INVALID_TARGET",
            details={"target": str(target)}
        )

class CombatNotStartedError(CombatException):
    """战斗未开始错误."""
    
    def __init__(self):
        super().__init__("你不在战斗中", code="COMBAT_NOT_STARTED")

class ItemException(GameException):
    """物品相关异常."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="ITEM_ERROR", **kwargs)

class CannotPickupError(ItemException):
    """无法拾取错误."""
    
    def __init__(self, item, reason: str):
        self.item = item
        self.reason = reason
        super().__init__(
            f"无法拾取{item.name}: {reason}",
            code="CANNOT_PICKUP",
            details={"item_key": item.key, "reason": reason}
        )

class OverweightError(ItemException):
    """超重错误."""
    
    def __init__(self, current: int, max_weight: int, item_weight: int):
        self.current = current
        self.max_weight = max_weight
        self.item_weight = item_weight
        super().__init__(
            f"负重已满 ({current}/{max_weight})，无法携带{item_weight}重量",
            code="OVERWEIGHT",
            details={
                "current": current,
                "max": max_weight,
                "item_weight": item_weight
            }
        )

class ValidationError(GameException):
    """数据验证错误."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            f"验证失败 [{field}]: {message}",
            code="VALIDATION_ERROR",
            details={"field": field}
        )
```

### 应用异常

**文件**: `src/game/typeclasses/item.py`

```python
from src.utils.exceptions import CannotPickupError, OverweightError

def can_pickup(self, character) -> tuple[bool, str]:
    """检查是否可以拾取."""
    try:
        # 检查负重
        if not character.can_carry(self):
            current = character.get_current_weight()
            max_w = character.get_max_weight()
            raise OverweightError(current, max_w, self.weight)
        
        return True, ""
    
    except OverweightError:
        raise  # 直接抛出
    except Exception as e:
        # 包装未知异常
        raise CannotPickupError(self, str(e)) from e
```

---

## ARCH-009: 输入验证加强

### 创建验证模块

**文件**: `src/utils/validators.py`

```python
"""输入验证工具."""

import re
from typing import Any, Callable, Pattern
from functools import wraps

class ValidationError(ValueError):
    """验证错误."""
    pass

class Validator:
    """验证器基类."""
    
    def __init__(self, message: str = None):
        self.message = message
    
    def validate(self, value: Any) -> Any:
        """验证值，返回转换后的值或抛出异常."""
        raise NotImplementedError

class LengthValidator(Validator):
    """长度验证器."""
    
    def __init__(self, min_len: int = 0, max_len: int = None, message: str = None):
        super().__init__(message)
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"期望字符串，得到{type(value).__name__}")
        
        length = len(value)
        
        if length < self.min_len:
            raise ValidationError(
                self.message or f"长度不能少于{self.min_len}"
            )
        
        if self.max_len is not None and length > self.max_len:
            raise ValidationError(
                self.message or f"长度不能超过{self.max_len}"
            )
        
        return value

class RegexValidator(Validator):
    """正则验证器."""
    
    def __init__(self, pattern: Pattern | str, message: str = None):
        super().__init__(message)
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
    
    def validate(self, value: str) -> str:
        if not self.pattern.match(value):
            raise ValidationError(
                self.message or f"格式不匹配模式: {self.pattern.pattern}"
            )
        return value

class RangeValidator(Validator):
    """范围验证器."""
    
    def __init__(self, min_val: int = None, max_val: int = None, message: str = None):
        super().__init__(message)
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, value: int | float) -> int | float:
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"期望数字，得到{type(value).__name__}")
        
        if self.min_val is not None and num < self.min_val:
            raise ValidationError(f"不能小于{self.min_val}")
        
        if self.max_val is not None and num > self.max_val:
            raise ValidationError(f"不能大于{self.max_val}")
        
        return value

# 预定义验证器
KeyValidator = RegexValidator(
    r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    "key只能包含字母数字下划线，且不能以数字开头"
)

NameValidator = LengthValidator(min_len=1, max_len=50)

PositiveIntValidator = RangeValidator(min_val=1)

class InputSanitizer:
    """输入清理器."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """清理字符串输入."""
        if not isinstance(value, str):
            value = str(value)
        
        # 移除控制字符（保留换行制表）
        value = ''.join(
            c for c in value 
            if c.isprintable() or c in '\n\t'
        )
        
        # 截断过长输入
        return value[:max_length]
    
    @staticmethod
    def sanitize_command_args(args: str) -> str:
        """清理命令参数."""
        # 基础清理
        args = InputSanitizer.sanitize_string(args, max_length=1000)
        
        # 防止命令注入
        dangerous = [';', '&&', '||', '|', '`', '$', '<', '>']
        for char in dangerous:
            args = args.replace(char, '')
        
        return args.strip()

# 装饰器
def validated(validator: Validator):
    """参数验证装饰器."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 验证第一个参数（通常是value）
            if args:
                validated_value = validator.validate(args[0])
                args = (validated_value,) + args[1:]
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 应用验证

**文件**: `src/engine/commands/command.py`

```python
from src.utils.validators import InputSanitizer, ValidationError

class Command:
    def parse(self, args: str) -> bool:
        """解析并验证参数."""
        try:
            # 清理参数
            sanitized = InputSanitizer.sanitize_command_args(args)
            
            # 长度验证
            if len(sanitized) > 1000:
                self.caller.msg("参数过长，最多1000字符")
                return False
            
            self.args = sanitized
            return True
            
        except Exception as e:
            logger.error(f"参数解析失败: {e}")
            self.caller.msg("参数格式错误")
            return False
```

---

*执行手册完成*

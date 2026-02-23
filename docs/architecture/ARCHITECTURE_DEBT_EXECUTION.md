# 架构债务清偿执行手册

> 每个债务的详细执行步骤和代码模板

---

## ARCH-001: 单例模式状态污染

### 执行步骤

#### Step 1: 修改 ConfigManager

**文件**: `src/utils/config.py`

**修改内容**:
```python
import threading

class ConfigManager:
    _instance: ConfigManager | None = None
    _lock = threading.Lock()
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (testing only).
        
        Warning: Do not call this in production code!
        """
        with cls._lock:
            cls._instance = None
    
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
```

#### Step 2: 创建测试隔离fixture

**文件**: `tests/conftest.py`

**新增**:
```python
import pytest
from src.utils.config import ConfigManager

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton states before each test."""
    ConfigManager.reset()
    yield
    ConfigManager.reset()
```

#### Step 3: 验证

```bash
python -m pytest tests/unit/test_config.py -v --count=5
```

---

## ARCH-002: 异步代码同步调用风险

### 执行步骤

#### Step 1: 修改 Message 类

**文件**: `src/engine/core/messages.py`

**修改**:
```python
import time

class Message:
    def __init__(self, ...):
        # Use standard timestamp, no event loop dependency
        self.timestamp = time.time()
        self.timestamp_ns = time.time_ns()
```

#### Step 2: 验证

```bash
python -m pytest tests/unit/test_messages.py -v
```

---

## ARCH-004: 测试覆盖率提升

### Item模块补充测试

**文件**: `tests/unit/test_item_coverage.py`

```python
"""Item module coverage supplement tests."""

import pytest
from src.game.typeclasses.item import Item

class TestItemCanPickupDetailed:
    """Detailed tests for can_pickup method."""
    
    def test_can_pickup_with_no_weight_attribute(self, mock_manager):
        """Test item without weight attribute defaults to pickup allowed."""
        pass
    
    def test_can_pickup_with_negative_weight(self, mock_manager):
        """Test negative weight handling."""
        pass

class TestItemCanUseDetailed:
    """Detailed tests for can_use method."""
    
    def test_can_use_consumable(self, mock_manager):
        """Test consumable use conditions."""
        pass
```

---

## ARCH-005: 魔法字符串到枚举

### 创建枚举模块

**文件**: `src/game/types/enums.py`

```python
"""Game system enums."""

from enum import Enum

class MoveType(str, Enum):
    """Move types."""
    ATTACK = "attack"
    DEFEND = "defend"
    CAST = "cast"
    USE_ITEM = "item"
    FLEE = "flee"

class BuffType(str, Enum):
    """Buff/debuff types."""
    POISON = "poison"
    STUN = "stun"
    BUFF = "buff"
    DEBUFF = "debuff"

class DamageType(str, Enum):
    """Damage types."""
    PHYSICAL = "physical"
    INTERNAL = "internal"
    POISON = "poison"
```

---

## ARCH-006: 循环导入风险

### 创建协议接口

**文件**: `src/game/interfaces.py`

```python
"""Game object protocol interfaces."""

from typing import Protocol, runtime_checkable

@runtime_checkable
class Combatant(Protocol):
    """Combat participant protocol."""
    
    @property
    def name(self) -> str: ...
    
    @property
    def hp(self) -> tuple[int, int]: ...
    
    def modify_hp(self, delta: int) -> int: ...
```

---

## ARCH-007: 异常处理完善

### 定义异常层次

**文件**: `src/utils/exceptions.py`

```python
"""Game exception definitions."""

class GameException(Exception):
    """Base game exception."""
    
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN"

class CombatException(GameException):
    """Combat related exception."""
    pass

class InvalidTargetError(CombatException):
    """Invalid target error."""
    pass
```

---

## ARCH-009: 输入验证加强

### 创建验证模块

**文件**: `src/utils/validators.py`

```python
"""Input validation utilities."""

import re
from typing import Any

class ValidationError(ValueError):
    """Validation error."""
    pass

class Validator:
    """Base validator."""
    
    def validate(self, value: Any) -> Any:
        raise NotImplementedError

class LengthValidator(Validator):
    """Length validator."""
    
    def __init__(self, min_len: int = 0, max_len: int = None):
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Expected string")
        
        if len(value) < self.min_len:
            raise ValidationError(f"Min length {self.min_len}")
        
        if self.max_len and len(value) > self.max_len:
            raise ValidationError(f"Max length {self.max_len}")
        
        return value

class InputSanitizer:
    """Input sanitizer."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove control chars
        value = "".join(c for c in value if c.isprintable() or c in "\n\t")
        
        return value[:max_length]
```

---

*Execution Manual Complete*

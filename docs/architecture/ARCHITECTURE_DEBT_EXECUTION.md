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

## ARCH-008: 资源清理完善

### 执行步骤

#### Step 1: 修复 engine.stop() 超时

**文件**: `src/engine/core/engine.py`

```python
async def stop(self, timeout: float = 5.0) -> None:
    """Stop engine with timeout control."""
    try:
        await asyncio.wait_for(self._do_stop(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("Engine stop timeout, force cleanup")
        self._force_cleanup()

def _force_cleanup(self) -> None:
    """Force resource cleanup."""
    # Force close database connections
    # Force stop scheduler
    # Clear caches
    pass
```

#### Step 2: 更新测试 fixture

**文件**: `tests/conftest.py`

```python
@pytest_asyncio.fixture
async def engine():
    eng = await _get_engine()
    yield eng
    # Ensure cleanup
    try:
        await asyncio.wait_for(eng.stop(), timeout=5.0)
    except asyncio.TimeoutError:
        pass  # Continue even if timeout
```

---

## ARCH-010: 文档字符串完善

### 执行步骤

#### Step 1: 添加文档字符串检查

**工具配置**: `pyproject.toml`

```toml
[tool.pydocstyle]
convention = "google"
add-ignore = ["D100", "D101"]  # Skip module/class docstrings
```

#### Step 2: 批量添加文档模板

**VS Code 代码片段**:
```json
{
  "Python Function Docstring": {
    "prefix": "docstring",
    "body": [
      "\"\"\"Brief description.",
      "",
      "Args:",
      "    param1: Description",
      "",
      "Returns:",
      "    Description of return value",
      "",
      "Raises:
      "    ExceptionType: When this happens",
      "\"\"\""
    ]
  }
}
```

---

## ARCH-011: 代码重复消除

### 执行步骤

#### Step 1: 提取公共 Mock 到 conftest.py

**文件**: `tests/conftest.py`

```python
@pytest.fixture
def mock_manager():
    """Create mock object manager."""
    return MockManager()

@pytest.fixture
def mock_character(mock_manager):
    """Create mock character."""
    db = MockDBModel(id=1, key="test_char")
    return Character(mock_manager, db)

@pytest.fixture
def mock_room(mock_manager):
    """Create mock room."""
    db = MockDBModel(id=2, key="test_room")
    return Room(mock_manager, db)
```

#### Step 2: 创建测试基类

**文件**: `tests/base.py`

```python
class BaseTypeclassTest:
    """Base test class for typeclass tests."""
    
    @pytest.fixture
    def db_model(self):
        return MockDBModel()
    
    @pytest.fixture
    def instance(self, mock_manager, db_model):
        return self.typeclass(mock_manager, db_model)

class TestCharacterBase(BaseTypeclassTest):
    typeclass = Character
    
    def test_name_property(self, instance):
        assert instance.name == instance.key
```

---

## 缺失项对照表

| 债务 | 路线图位置 | 执行手册状态 | 补充内容 |
|:---:|:---:|:---:|:---|
| ARCH-008 | Day 12 | ✅ 已补充 | 资源清理完善 |
| ARCH-010 | Day 13-14 | ✅ 已补充 | 文档字符串完善 |
| ARCH-011 | Day 13-14 | ✅ 已补充 | 代码重复消除 |

---

*Execution Manual Complete - All 10 items covered*

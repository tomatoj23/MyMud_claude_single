# 架构债务清偿路线图

> 系统化的架构债务清偿计划

**版本**: 1.0  
**创建日期**: 2026-02-23  
**预计周期**: 3周  
**影响范围**: 核心引擎 + 游戏系统

---

## 执行摘要

### 债务清单

| 级别 | 数量 | 风险 | 清偿策略 |
|:---:|:---:|:---:|:---|
| 🔴 高 | 2项 | 系统稳定性 | 立即修复 |
| 🟡 中 | 7项 | 维护成本 | 迭代重构 |
| 🟢 低 | 4项 | 技术栈演进 | 长期跟踪 |

### 清偿原则

1. **稳定性优先**: 先修复导致系统不稳定的问题
2. **测试保障**: 每项债务清偿必须有测试覆盖
3. **渐进重构**: 避免大规模重写，小步迭代
4. **文档同步**: 代码变更同步更新文档

---

## 债务依赖关系图

```
                    ┌─────────────────┐
                    │   ARCH-001      │
                    │ 单例状态污染    │
                    │   [阻塞]        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ARCH-002      │
                    │ 异步调用风险    │
                    │   [阻塞]        │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   ARCH-004      │  │   ARCH-006      │  │   ARCH-009      │
│ 测试覆盖提升    │  │ 循环导入风险    │  │ 输入验证加强    │
│   [基础]        │  │   [设计]        │  │   [安全]        │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                   │                   │
         │                   ▼                   │
         │          ┌─────────────────┐          │
         │          │   ARCH-005      │          │
         │          │ 魔法字符串      │          │
         │          │   [代码质量]    │          │
         │          └────────┬────────┘          │
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ARCH-007      │
                    │ 异常处理完善    │
                    │   [健壮性]      │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────────┐ ┌────────┐ ┌────────────────┐
     │  ARCH-008      │ │ARCH-010│ │  ARCH-011      │
     │ 资源清理       │ │文档    │ │ 代码重复       │
     │ [测试]         │ │[维护]  │ │ [重构]         │
     └────────────────┘ └────────┘ └────────────────┘
```

---

## 阶段一: 基础稳定性修复 (Week 1)

### 目标
修复影响系统稳定性的高优先级债务，确保测试环境可靠。

### 任务清单

#### Day 1-2: ARCH-001 单例模式状态污染

**问题分析**:
```python
# config.py 中的单例实现
class ConfigManager:
    _instance: ConfigManager | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**风险**:
- 测试间状态相互污染
- 无法并行运行测试
- `test_detect_environment_frozen` 偶发失败

**解决方案**:

步骤1: 添加重置方法
```python
class ConfigManager:
    _instance: ConfigManager | None = None
    
    @classmethod
    def reset(cls) -> None:
        """重置单例实例（仅用于测试）."""
        cls._instance = None
    
    @classmethod
    def get_instance(cls) -> ConfigManager:
        """获取单例实例."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

步骤2: 添加测试隔离fixture
```python
# conftest.py
@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试前重置单例状态."""
    # 重置所有单例
    ConfigManager.reset()
    MessageBus.reset()  # 如果存在
    yield
    # 测试后清理
    ConfigManager.reset()
```

步骤3: 修改所有测试使用fixture
```python
def test_something(reset_singletons):
    # 现在单例状态是干净的
    config = ConfigManager()
    ...
```

**验收标准**:
- [ ] `test_detect_environment_frozen` 连续运行10次通过
- [ ] 新增测试隔离fixture
- [ ] 所有现有测试使用新fixture
- [ ] 文档更新

**工作量**: 8小时  
**风险**: 低 - 向后兼容

---

#### Day 3: ARCH-002 异步代码同步调用风险

**问题分析**:
```python
# messages.py:57
class Message:
    def __init__(self, ...):
        self.timestamp = asyncio.get_event_loop().time()
```

**风险**:
- 在没有事件循环的线程中调用会抛出 `RuntimeError`
- 测试 `test_msg_no_caller` 曾因此失败

**解决方案**:

步骤1: 使用time.time()替代
```python
import time

class Message:
    def __init__(self, ...):
        # 使用标准时间戳，不依赖事件循环
        self.timestamp = time.time()
```

步骤2: 如果需要纳秒精度
```python
import time

class Message:
    def __init__(self, ...):
        # 纳秒级时间戳
        self.timestamp_ns = time.time_ns()
        self.timestamp = self.timestamp_ns / 1e9
```

步骤3: 添加兼容性处理
```python
class Message:
    def __init__(self, ...):
        try:
            # 优先使用asyncio时间（如果在协程中）
            self.timestamp = asyncio.get_event_loop().time()
        except RuntimeError:
            # 回退到标准时间
            self.timestamp = time.time()
```

**验收标准**:
- [ ] `test_msg_no_caller` 稳定通过
- [ ] 非协程线程中创建Message不抛异常
- [ ] 时间戳精度满足需求

**工作量**: 4小时  
**风险**: 极低 - 简单替换

---

#### Day 4-5: ARCH-004 测试覆盖率提升

**问题模块**:

| 模块 | 覆盖率 | 目标 | 缺失内容 |
|:---|:---:|:---:|:---|
| item.py | 64% | 90% | can_pickup, can_use, on_use |
| room.py | 75% | 90% | get_contents_async, at_desc |
| pathfinding.py | 78% | 90% | find_path_to_key, find_path_to_coords |
| default.py | 55% | 80% | 默认命令 |
| config.py | 76% | 90% | 边界条件 |

**解决方案**:

步骤1: Item模块补充测试
```python
# tests/unit/test_item_coverage.py
class TestItemCanPickup:
    """Item.can_pickup 覆盖率补充测试."""
    
    def test_can_pickup_with_weight_check(self):
        """测试负重检查."""
        # 已部分实现
        ...
    
    def test_can_pickup_overweight(self):
        """测试超重时无法拾取."""
        ...
    
    def test_can_use_consumable(self):
        """测试消耗品使用."""
        ...
    
    def test_on_use_healing_herb(self):
        """测试草药使用效果."""
        ...
```

步骤2: Room模块补充测试
```python
# tests/unit/test_room_coverage.py
class TestRoomGetContents:
    """Room.get_contents_async 测试."""
    
    @pytest.mark.asyncio
    async def test_get_contents_async(self):
        """测试异步获取内容."""
        ...
    
    def test_at_desc_with_contents(self):
        """测试房间描述包含内容."""
        ...
```

步骤3: 默认命令补充测试
```python
# tests/unit/test_default_commands_coverage.py
class TestDefaultCommandCoverage:
    """默认命令覆盖率测试."""
    
    @pytest.mark.asyncio
    async def test_cmd_look_with_target(self):
        """测试查看指定目标."""
        ...
    
    @pytest.mark.asyncio
    async def test_cmd_go_with_invalid_direction(self):
        """测试无效方向移动."""
        ...
```

**验收标准**:
- [ ] item.py 覆盖率 >= 90%
- [ ] room.py 覆盖率 >= 90%
- [ ] pathfinding.py 覆盖率 >= 90%
- [ ] default.py 覆盖率 >= 80%
- [ ] config.py 覆盖率 >= 90%

**工作量**: 12小时  
**风险**: 低 - 只添加测试，不改代码

---

## 阶段二: 代码质量重构 (Week 2)

### 目标
提升代码可维护性，消除设计债务。

### 任务清单

#### Day 6-7: ARCH-006 循环导入风险

**问题分析**:
```python
# combat/core.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.game.typeclasses.character import Character
```

**风险**:
- 运行时类型信息丢失
- 某些反射操作可能失败

**解决方案**:

步骤1: 评估是否真的需要循环导入
```python
# 检查实际使用情况
grep -r "from.*character import Character" src/game/combat/
# 如果只在类型注解中使用，保留TYPE_CHECKING
# 如果在运行时中使用，需要重构
```

步骤2: 创建接口抽象层
```python
# src/game/interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol

class Combatant(Protocol):
    """战斗参与者协议."""
    
    @property
    def name(self) -> str: ...
    
    @property
    def hp(self) -> int: ...
    
    def modify_hp(self, delta: int) -> int: ...

class AIController(Protocol):
    """AI控制器协议."""
    
    async def decide_action(self, context: CombatContext) -> CombatAction: ...
```

步骤3: 使用协议替代具体类型
```python
# combat/core.py
from src.game.interfaces import Combatant

async def process_ai_turns(self, combatant: Combatant) -> None:
    # 现在不依赖具体的Character类
    ...
```

**验收标准**:
- [ ] 消除所有运行时循环导入
- [ ] 创建协议接口
- [ ] 所有测试通过

**工作量**: 12小时  
**风险**: 中 - 涉及多处代码修改

---

#### Day 8: ARCH-005 魔法字符串 → 枚举

**问题分析**:
```python
# 示例 - 魔法字符串
if move.type == "attack":  # 魔法字符串
if buff.buff_type == "poison":  # 魔法字符串
```

**解决方案**:

步骤1: 创建枚举定义
```python
# src/game/types/enums.py
from enum import Enum, auto

class MoveType(Enum):
    """招式类型."""
    ATTACK = "attack"
    DEFEND = "defend"
    CAST = "cast"
    ITEM = "item"
    FLEE = "flee"

class BuffType(Enum):
    """BUFF类型."""
    POISON = "poison"
    STUN = "stun"
    BUFF = "buff"
    DEBUFF = "debuff"

class DamageType(Enum):
    """伤害类型."""
    PHYSICAL = "physical"
    INTERNAL = "internal"
    POISON = "poison"
    FIRE = "fire"
    COLD = "cold"
```

步骤2: 批量替换字符串
```python
# 替换前
if move.type == "attack":

# 替换后
if move.type == MoveType.ATTACK:
```

步骤3: 添加兼容性转换
```python
class MoveType(Enum):
    @classmethod
    def from_string(cls, value: str) -> "MoveType":
        """从字符串创建枚举（兼容旧数据）."""
        try:
            return cls(value)
        except ValueError:
            # 处理旧数据映射
            mapping = {
                "attack": cls.ATTACK,
                "defend": cls.DEFEND,
            }
            return mapping.get(value, cls.ATTACK)
```

**验收标准**:
- [ ] 创建所有必要枚举
- [ ] 替换所有魔法字符串
- [ ] 旧数据兼容性处理
- [ ] 静态类型检查通过

**工作量**: 8小时  
**风险**: 中 - 需要数据迁移

---

#### Day 9: ARCH-007 异常处理完善

**问题分析**:
```python
# 过于宽泛的异常捕获
try:
    result = await some_operation()
except Exception as e:  # 过于宽泛
    logger.error(f"操作失败: {e}")
```

**解决方案**:

步骤1: 定义分层异常体系
```python
# src/utils/exceptions.py

class GameException(Exception):
    """游戏基础异常."""
    pass

class CombatException(GameException):
    """战斗相关异常."""
    pass

class InvalidTargetError(CombatException):
    """无效目标错误."""
    pass

class CombatNotStartedError(CombatException):
    """战斗未开始错误."""
    pass

class ItemException(GameException):
    """物品相关异常."""
    pass

class CannotPickupError(ItemException):
    """无法拾取错误."""
    pass

class OverweightError(ItemException):
    """超重错误."""
    pass
```

步骤2: 精细化异常捕获
```python
# 替换前
try:
    result = await combat.attack(target)
except Exception as e:
    logger.error(f"攻击失败: {e}")

# 替换后
from src.utils.exceptions import InvalidTargetError, CombatNotStartedError

try:
    result = await combat.attack(target)
except InvalidTargetError as e:
    logger.warning(f"无效目标: {e}")
    character.msg("你无法攻击这个目标。")
except CombatNotStartedError:
    logger.error("战斗未开始")
    character.msg("你不在战斗中。")
except CombatException as e:
    logger.error(f"战斗操作失败: {e}")
    character.msg("战斗操作失败。")
```

步骤3: 添加异常上下文
```python
class CannotPickupError(ItemException):
    def __init__(self, item: Item, reason: str):
        self.item = item
        self.reason = reason
        super().__init__(f"无法拾取{item.name}: {reason}")
```

**验收标准**:
- [ ] 定义完整的异常层次结构
- [ ] 替换所有宽泛的except Exception
- [ ] 添加异常上下文信息
- [ ] 文档更新

**工作量**: 8小时  
**风险**: 中 - 可能影响错误处理逻辑

---

#### Day 10-11: ARCH-009 输入验证加强

**问题分析**:
```python
def parse(self, args: str) -> bool:
    """解析参数。"""
    self.args = args  # 无验证
    return True
```

**解决方案**:

步骤1: 创建验证器基类
```python
# src/utils/validators.py
from abc import ABC, abstractmethod
from typing import Any, Callable

class Validator(ABC):
    @abstractmethod
    def validate(self, value: Any) -> tuple[bool, str]:
        """验证值，返回(是否有效, 错误信息)."""
        pass

class LengthValidator(Validator):
    def __init__(self, min_len: int = 0, max_len: int = 1000):
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: str) -> tuple[bool, str]:
        if not isinstance(value, str):
            return False, "值必须是字符串"
        if len(value) < self.min_len:
            return False, f"长度不能少于{self.min_len}"
        if len(value) > self.max_len:
            return False, f"长度不能超过{self.max_len}"
        return True, ""

class TypeValidator(Validator):
    def __init__(self, expected_type: type):
        self.expected_type = expected_type
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if not isinstance(value, self.expected_type):
            return False, f"类型错误，期望{self.expected_type.__name__}"
        return True, ""

class CommandSanitizer:
    """命令参数清理器."""
    
    @staticmethod
    def sanitize(args: str) -> str:
        """清理命令参数，防止注入攻击."""
        # 移除控制字符
        sanitized = ''.join(c for c in args if c.isprintable() or c.isspace())
        # 限制长度
        return sanitized[:1000]
    
    @staticmethod
    def validate_identifier(name: str) -> tuple[bool, str]:
        """验证标识符（key/name）."""
        if not name:
            return False, "标识符不能为空"
        if len(name) > 50:
            return False, "标识符过长"
        # 只允许字母数字下划线
        if not all(c.isalnum() or c == '_' for c in name):
            return False, "标识符只能包含字母数字下划线"
        return True, ""
```

步骤2: 应用验证到Command
```python
class Command:
    def parse(self, args: str) -> bool:
        """解析并验证参数."""
        # 清理参数
        sanitized = CommandSanitizer.sanitize(args)
        
        # 长度验证
        validator = LengthValidator(max_len=1000)
        is_valid, error = validator.validate(sanitized)
        if not is_valid:
            self.caller.msg(f"参数错误: {error}")
            return False
        
        self.args = sanitized
        return True
```

步骤3: 数据库输入验证
```python
class ObjectManager:
    async def create(self, typeclass_path: str, key: str, **kwargs) -> TypeclassBase:
        # 验证key
        is_valid, error = CommandSanitizer.validate_identifier(key)
        if not is_valid:
            raise ValueError(f"无效的key: {error}")
        
        # 验证typeclass_path
        if not typeclass_path.startswith("src."):
            raise ValueError("无效的typeclass_path")
        
        ...
```

**验收标准**:
- [ ] 所有用户输入都经过验证
- [ ] 注入攻击防护（命令/脚本/SQL）
- [ ] 长度/类型/格式验证
- [ ] 友好的错误提示

**工作量**: 12小时  
**风险**: 中 - 需要全面测试

---

## 阶段三: 可维护性优化 (Week 3)

### 目标
提升代码可维护性，完善文档和测试。

### 任务清单

#### Day 12: ARCH-008 资源清理完善

**问题分析**:
```python
# conftest.py
@pytest_asyncio.fixture
async def engine():
    eng = await _get_engine()
    yield eng
    # 注意：不调用engine.stop()以避免超时
```

**解决方案**:

步骤1: 修复engine.stop()超时问题
```python
# src/engine/core/engine.py
async def stop(self, timeout: float = 5.0) -> None:
    """停止引擎，带超时控制."""
    try:
        await asyncio.wait_for(self._do_stop(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("引擎停止超时，强制清理")
        self._force_cleanup()

def _force_cleanup(self) -> None:
    """强制清理资源."""
    # 强制关闭数据库连接
    # 强制停止调度器
    # 清理缓存
    ...
```

步骤2: 添加资源清理fixture
```python
# conftest.py
@pytest_asyncio.fixture
async def engine():
    eng = await _get_engine()
    yield eng
    # 确保清理
    try:
        await asyncio.wait_for(eng.stop(), timeout=5.0)
    except asyncio.TimeoutError:
        pass  # 即使超时也继续
```

步骤3: 添加资源监控
```python
class ResourceMonitor:
    """资源监控器."""
    
    def __init__(self):
        self.engines: set[GameEngine] = set()
    
    def register(self, engine: GameEngine) -> None:
        self.engines.add(engine)
    
    async def cleanup_all(self) -> None:
        """清理所有资源."""
        for engine in list(self.engines):
            try:
                await engine.stop()
            except Exception as e:
                logger.error(f"清理引擎失败: {e}")
            finally:
                self.engines.discard(engine)

# pytest钩子
@pytest.fixture(scope="session", autouse=True)
def cleanup_resources():
    yield
    # 会话结束时清理
    asyncio.run(ResourceMonitor().cleanup_all())
```

**验收标准**:
- [ ] 所有测试后资源正确释放
- [ ] 无数据库连接泄漏
- [ ] 无事件循环残留

**工作量**: 6小时  
**风险**: 低

---

#### Day 13-14: ARCH-010/011 文档和代码重复

**任务拆分**:

文档补充:
- 为所有公共方法添加docstring
- 补充参数说明
- 添加类型注解示例

代码重复消除:
- 提取公共mock到conftest.py
- 抽象测试基类
- 统一fixture命名

**验收标准**:
- [ ] 公共方法100%有docstring
- [ ] 测试代码重复率<10%
- [ ] 类型检查通过

**工作量**: 12小时  
**风险**: 极低

---

## 验收与回归 (Week 3 Day 15)

### 验收清单

- [ ] 所有测试通过 (1329个)
- [ ] 覆盖率目标达成 (总体>90%)
- [ ] 静态类型检查通过 (mypy)
- [ ] 代码风格检查通过 (ruff)
- [ ] 混沌测试通过
- [ ] 性能测试通过 (无回归)

### 回归测试

```bash
# 全量测试
pytest tests/ -x --tb=short

# 覆盖率检查
pytest tests/ --cov=src --cov-report=html --cov-fail-under=90

# 混沌测试
pytest tests/integration/test_chaos_*.py -v

# 静态检查
mypy src/ --strict
ruff check src/
black --check src/
```

---

## 风险缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|:---|:---:|:---:|:---|
| 重构引入Bug | 中 | 高 | 小步提交，每步全量测试 |
| 测试时间过长 | 中 | 中 | 并行运行，选择性测试 |
| 数据兼容性问题 | 低 | 高 | 兼容性转换层 |
| 团队不熟悉新代码 | 中 | 中 | 代码审查，知识分享 |

---

## 附录

### A. 债务快速参考

```
高优先级 (立即):
- ARCH-001: 单例模式
- ARCH-002: 异步调用

中优先级 (本周):
- ARCH-004: 测试覆盖
- ARCH-005: 魔法字符串
- ARCH-006: 循环导入
- ARCH-007: 异常处理
- ARCH-008: 资源清理
- ARCH-009: 输入验证

低优先级 (下周):
- ARCH-010: 文档
- ARCH-011: 代码重复
- ARCH-012~014: 性能/类型/缓存
```

### B. 工具配置

```toml
# pyproject.toml 更新
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*"]

[tool.coverage.report]
fail_under = 90
show_missing = true

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

---

*最后更新: 2026-02-23*

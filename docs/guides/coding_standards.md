# 开发规范

> 本文档定义金庸武侠MUD项目的开发规范。

---

## 代码风格

### Python代码规范

本项目遵循 **PEP 8** 规范，使用以下工具强制执行：

- **Black**: 代码格式化
- **Ruff**: 静态检查
- **mypy**: 类型检查

### 行长度

最大行长度：**100字符**

```python
# 正确
result = some_function(
    arg1=value1,
    arg2=value2,
    arg3=value3
)

# 错误 - 超过100字符
result = some_function(arg1=value1, arg2=value2, arg3=value3, arg4=value4, arg5=value5)
```

### 命名规范

| 类型 | 规范 | 示例 |
|:---|:---|:---|
| 类名 | PascalCase | `GameEngine`, `TypeclassBase` |
| 函数/方法 | snake_case | `process_input`, `calculate_damage` |
| 常量 | UPPER_SNAKE_CASE | `MAX_LEVEL`, `DEFAULT_TIMEOUT` |
| 私有属性 | _leading_underscore | `_is_dirty`, `_cache` |
| 模块名 | snake_case | `engine.py`, `typeclass.py` |

### 类型注解

所有函数必须添加类型注解：

```python
# 正确
def calculate_damage(
    attacker: Character,
    defender: Character,
    move: Move | None = None
) -> DamageResult:
    """计算伤害。"""
    ...

# 错误 - 缺少类型注解
def calculate_damage(attacker, defender, move=None):
    ...
```

### 文档字符串

所有公共类和方法必须包含文档字符串，使用 **Google风格**：

```python
class CombatCalculator:
    """战斗计算器。
    
    提供命中率、伤害值等战斗相关计算。
    
    Attributes:
        crit_rate: 暴击率基础值
        crit_damage: 暴击伤害倍率
    """
    
    def calculate_hit_rate(
        self,
        attacker: Character,
        defender: Character
    ) -> float:
        """计算命中率。
        
        Args:
            attacker: 攻击者
            defender: 防御者
            
        Returns:
            命中率（0.0-1.0）
            
        Raises:
            ValueError: 角色属性异常时抛出
        """
        ...
```

---

## 异步编程规范

### async/await使用

所有IO操作必须使用异步：

```python
# 正确
async def load_object(obj_id: int) -> TypeclassBase:
    async with db.session() as session:
        result = await session.get(ObjectModel, obj_id)
        return result

# 错误 - 阻塞IO
async def load_object(obj_id: int) -> TypeclassBase:
    session = db.session()  # 阻塞！
    return session.get(ObjectModel, obj_id)
```

### 事件循环

禁止手动创建事件循环，使用 `asyncio.run()`：

```python
# 正确
import asyncio

async def main():
    ...

if __name__ == "__main__":
    asyncio.run(main())

# 错误
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

---

## 错误处理

### 异常使用

- 使用具体异常类型，避免裸 `except`
- 自定义异常继承自 `Exception`

```python
# 正确
try:
    await engine.initialize()
except DatabaseError as e:
    logger.error(f"数据库初始化失败: {e}")
    raise EngineError("引擎初始化失败") from e

# 错误
try:
    await engine.initialize()
except:  # 捕获所有异常，包括KeyboardInterrupt
    pass
```

### 错误日志

使用 `logging` 模块，禁止 `print`：

```python
import logging

logger = logging.getLogger(__name__)

# 正确
logger.info("引擎启动成功")
logger.warning("缓存命中率低: %.2f", hit_rate)
logger.error("数据库连接失败", exc_info=True)

# 错误
print("引擎启动成功")
```

---

## 测试规范

### 测试结构

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestFeature:
    """功能测试类。"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建mock引擎。"""
        return Mock()
    
    def test_something(self, mock_engine):
        """测试某功能。"""
        # Arrange
        obj = MyClass(mock_engine)
        
        # Act
        result = obj.do_something()
        
        # Assert
        assert result == expected
```

### 测试命名

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    """测试异步功能。"""
    result = await async_function()
    assert result is not None
```

---

## Git提交规范

### 提交信息格式

```
<类型>: <简要描述>

<详细描述（可选）>

<相关Issue（可选）>
```

### 提交类型

| 类型 | 说明 |
|:---|:---|
| `feat` | 新功能 |
| `fix` | 修复Bug |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

### 提交示例

```bash
# 功能提交
git commit -m "feat: 添加战斗AI系统

实现基础AI决策逻辑，包括：
- 随机选择目标
- 根据血量决策行动
- 招式选择逻辑

Closes #123"

# 修复提交
git commit -m "fix: 修复战斗结束时经验计算错误

经验倍率应从1.0开始而非0.0"

# 文档提交
git commit -m "docs: 更新API文档"
```

---

## 项目结构规范

### 目录组织

```
src/
├── engine/          # 引擎核心（框架无关）
│   ├── core/        # 核心基类
│   ├── commands/    # 命令系统
│   ├── events/      # 事件调度
│   ├── database/    # 数据库
│   └── objects/     # 对象管理
├── game/            # 游戏实现（武侠相关）
│   ├── typeclasses/ # 类型类
│   ├── combat/      # 战斗系统
│   ├── npc/         # NPC系统
│   ├── quest/       # 任务系统
│   └── world/       # 世界系统
└── utils/           # 工具函数
```

### 导入规范

```python
# 标准库
import asyncio
from typing import Any

# 第三方库
import sqlalchemy
from PySide6 import QtWidgets

# 项目内部
from src.engine.core.engine import GameEngine
from src.game.typeclasses.character import Character
```

---

## 性能规范

### 数据库查询

- 使用 `selectinload` 避免N+1问题
- 批量操作使用 `executemany`
- 缓存频繁访问的数据

### 内存管理

- 避免循环引用
- 及时清理缓存
- 使用 `__slots__` 减少内存占用（可选）

---

## 安全规范

### 输入验证

- 所有用户输入必须验证
- 使用参数化查询防止SQL注入
- 转义HTML防止XSS

### 敏感数据

- 密码等敏感信息必须加密存储
- 配置文件不包含真实凭据
- 日志中不记录敏感信息

---

## 代码审查检查清单

### 提交前自检

- [ ] 代码通过 `black` 格式化
- [ ] 代码通过 `ruff` 检查
- [ ] 代码通过 `mypy` 类型检查
- [ ] 所有测试通过
- [ ] 新增代码有测试覆盖
- [ ] 文档已更新

### 审查重点

- [ ] 异步代码是否正确使用
- [ ] 错误处理是否完善
- [ ] 是否有资源泄漏风险
- [ ] 性能是否有明显问题
- [ ] 是否符合架构设计

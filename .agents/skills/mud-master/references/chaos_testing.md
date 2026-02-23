# 混沌测试方法论

## 概述

混沌测试（Chaos Testing）是通过模拟非理性、无逻辑、随机的用户行为来发现系统潜在问题的测试方法。

适用于单机游戏，测试各种异常操作序列、状态污染、时序混乱等场景。

## 测试分类

### 1. 随机命令输入测试

测试各种异常命令输入：

```python
random_commands = [
    "",                          # 空命令
    "   ",                       # 只有空格
    "!@#$%^&*()",               # 特殊字符
    "look look look",           # 重复命令
    "go nowhere",               # 无效方向
    "kill",                     # 缺少目标
    "use nonexistent_item",     # 不存在的物品
    "a" * 1000,                 # 超长命令
    "<script>alert('xss')>",    # 注入尝试
]
```

### 2. 非逻辑操作序列测试

不按正常流程使用功能：

```python
# 获得物品前就装备
await char.equip(item_not_in_inventory)

# 拾取前就使用物品
await item.on_use(char)  # item不在char背包里

# 与已死亡NPC对话
await dead_npc.talk(char)

# 未接受任务就完成
char.update_quest_progress("unaccepted_quest", 1)
```

### 3. 状态污染测试

在错误状态下尝试操作：

```python
# 死亡状态下执行操作
dead_char.equip(sword)
dead_char.move("north")

# 战斗中更换装备
char.in_combat = True
await char.equip(new_sword)

# 眩晕状态下移动
stunned_char.move("north")
```

### 4. 时序混乱测试

操作顺序完全随机：

```python
# 随机保存/加载时机
operations = [
    lambda: engine.objects.mark_dirty(char),
    lambda: engine.objects.save(char),
    lambda: engine.objects.load(char.id),
]

# 并发修改和保存
await asyncio.gather(
    modify_attrs(),
    save_repeatedly(),
)
```

### 5. 数据污染测试

使用异常数据调用API：

```python
# 损坏的属性类型
char.db._data = None
char.db._data = "string_instead_of_dict"

# 类型混淆
char.equip("string_instead_of_equipment")
char.equip(12345)

# 循环引用
char.db.set("self", char)
```

### 6. 边界条件爆炸测试

测试各种极端边界：

```python
# 数值边界
extreme_values = [
    0, -1, 2**31-1, -(2**31),
    2**63-1, -(2**63), 2**1024,
    float('inf'), float('-inf'), float('nan'),
]

# 字符串长度边界
for length in [0, 1, 10, 1000, 10000, 1000000]:
    char.db.set(f"str_{length}", "x" * length)

# 嵌套深度边界
depths = [0, 1, 10, 100, 500, 1000]
for depth in depths:
    nested = create_nested_dict(depth)
    char.db.set(f"nest_{depth}", nested)
```

## 混沌测试原则

### 1. 破坏性原则
- 测试应该尝试破坏系统
- 不遵循任何逻辑或规则
- 模拟最疯狂的用户行为

### 2. 异常容忍
- 测试本身应该捕获所有异常
- 记录但不因异常而失败
- 关注系统是否崩溃或数据损坏

### 3. 随机性
- 使用随机数据生成
- 随机操作序列
- 随机时序和并发

### 4. 边界探索
- 测试各种边界值
- 零值、负值、极大值
- 空值、None、特殊字符

## 实现示例

```python
import pytest
import random
import asyncio

class TestChaosPlayerBehavior:
    """混沌玩家行为测试"""
    
    @pytest.mark.asyncio
    async def test_random_command_inputs(self, engine):
        """测试随机命令输入"""
        for cmd in generate_random_commands(100):
            try:
                await engine.process_input(cmd)
            except Exception as e:
                # 记录但不失败
                print(f"Command '{cmd}' raised: {e}")
    
    @pytest.mark.asyncio
    async def test_rapid_random_commands(self, engine):
        """测试快速随机命令轰炸"""
        for _ in range(1000):
            cmd = random.choice(COMMANDS_POOL)
            try:
                await engine.process_input(cmd)
            except Exception as e:
                print(f"Rapid command failed: {e}")
    
    @pytest.mark.asyncio
    async def test_extreme_attribute_values(self, engine):
        """测试极端属性值"""
        char = await create_test_character(engine)
        
        extreme_values = {
            "hp": float('inf'),
            "level": float('nan'),
            "exp": 1e308,
            "gold": -1e308,
        }
        
        for key, value in extreme_values.items():
            try:
                char.db.set(key, value)
            except Exception as e:
                print(f"Set {key}={value}: {e}")
```

## 混沌测试的价值

1. **发现隐藏Bug** - 正常测试难以发现的边界情况
2. **验证鲁棒性** - 系统对异常输入的处理能力
3. **安全测试** - 注入攻击、数据污染防护
4. **性能测试** - 极端条件下的性能表现
5. **用户体验** - 确保疯狂操作不会损坏存档

## 运行混沌测试

```bash
# 运行所有混沌测试
pytest tests/integration/test_chaos_*.py -v

# 运行特定类别
pytest tests/integration/test_chaos_player_behavior.py -v
pytest tests/integration/test_api_chaos.py -v
pytest tests/integration/test_edge_case_explosion.py -v

# 排除慢测试
pytest tests/integration/test_chaos_*.py -m "not slow" -v
```

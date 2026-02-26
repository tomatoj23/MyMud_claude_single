# 金庸武侠MUD架构改进实施手册

**版本**: 1.0  
**日期**: 2026-02-23  
**配套文档**: ROADMAP.md, ARCHITECTURE_ANALYSIS.md

---

## 目录

1. [准备工作](#1-准备工作)
2. [战斗系统事务保护实施](#2-战斗系统事务保护实施)
3. [Mixin方法前缀规范实施](#3-mixin方法前缀规范实施)
4. [状态一致性检查实施](#4-状态一致性检查实施)
5. [战斗策略模式重构实施](#5-战斗策略模式重构实施)
6. [循环依赖解耦实施](#6-循环依赖解耦实施)
7. [组件模式试点实施](#7-组件模式试点实施)
8. [配置外置化实施](#8-配置外置化实施)
9. [测试规范](#9-测试规范)
10. [故障排除](#10-故障排除)

---

## 1. 准备工作

### 1.1 环境检查

```bash
# 确保所有测试通过
python -m pytest tests/ -v --tb=short

# 确保无未提交代码
git status

# 创建改进分支
git checkout -b refactor/architecture-improvement
```

### 1.2 备份策略

```bash
# 创建备份分支
git branch backup/pre-architecture-improvement

# 或者创建tag
git tag -a v1.0-pre-improvement -m "架构改进前版本"
```

### 1.3 开发环境

```python
# 安装开发依赖
pip install -e ".[dev]"

# 验证环境
python -c "from src.engine.core.engine import GameEngine; print('OK')"
```

---

## 2. 战斗系统事务保护实施

### 2.1 创建事务模块

**文件**: `src/game/combat/transaction.py`

```python
"""战斗事务保护模块.

提供战斗操作的事务保护，支持回滚机制。
"""

from __future__ import annotations

import copy
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Combatant


@dataclass
class StateSnapshot:
    """状态快照"""
    obj_id: int
    attributes: dict[str, Any]


@dataclass
class TransactionLog:
    """事务日志"""
    snapshots: list[StateSnapshot] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False


class CombatTransaction:
    """战斗事务.
    
    支持快照、回滚、部分失败处理。
    
    使用示例:
        with session.transaction() as txn:
            target.hp -= damage
            attacker.mp -= cost
            txn.commit()  # 明确提交
    """
    
    def __init__(self):
        self._log = TransactionLog()
        self._snapshots: dict[int, dict[str, Any]] = {}
    
    def snapshot(self, obj: Any, attributes: list[str] | None = None):
        """记录对象状态快照.
        
        Args:
            obj: 要快照的对象
            attributes: 要记录的属性列表，None表示所有可序列化属性
        """
        obj_id = id(obj)
        if obj_id in self._snapshots:
            return  # 已记录过
        
        if attributes is None:
            # 自动检测关键属性
            attributes = ['hp', 'mp', 'ep', 'status']
        
        snapshot = {}
        for attr in attributes:
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                # 深拷贝防止引用问题
                try:
                    snapshot[attr] = copy.deepcopy(value)
                except (TypeError, copy.Error):
                    snapshot[attr] = value
        
        self._snapshots[obj_id] = snapshot
        self._log.snapshots.append(StateSnapshot(obj_id, snapshot))
    
    def commit(self):
        """提交事务，清除快照"""
        self._log.committed = True
        self._snapshots.clear()
    
    def rollback(self):
        """回滚到快照状态"""
        for obj_id, snapshot in self._snapshots.items():
            obj = self._get_object_by_id(obj_id)
            if obj:
                for attr, value in snapshot.items():
                    setattr(obj, attr, value)
        
        self._log.rolled_back = True
        self._snapshots.clear()
    
    def _get_object_by_id(self, obj_id: int) -> Any | None:
        """通过id获取对象（简化实现）"""
        # 实际实现需要维护对象引用映射
        import gc
        for obj in gc.get_objects():
            if id(obj) == obj_id:
                return obj
        return None
    
    @contextmanager
    def auto_rollback(self):
        """自动回滚上下文管理器"""
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise


class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        self._active_transactions: list[CombatTransaction] = []
    
    @contextmanager
    def begin(self):
        """开始新事务"""
        txn = CombatTransaction()
        self._active_transactions.append(txn)
        try:
            yield txn
            if not txn._log.committed and not txn._log.rolled_back:
                txn.commit()
        except Exception:
            txn.rollback()
            raise
        finally:
            self._active_transactions.remove(txn)
```

### 2.2 集成到CombatSession

**修改**: `src/game/combat/core.py`

```python
from .transaction import CombatTransaction, TransactionManager

class CombatSession:
    def __init__(self, ...):
        # ... 现有代码 ...
        self._txn_manager = TransactionManager()
    
    @contextmanager
    def transaction(self):
        """提供事务保护上下文"""
        with self._txn_manager.begin() as txn:
            yield txn
    
    async def _execute_move(self, combatant: Combatant, args: dict) -> tuple[bool, str]:
        """执行招式（带事务保护）"""
        target = self._get_target(combatant, args.get("target_id"))
        if not target:
            return False, "目标不存在"
        
        move = args.get("move")
        kungfu = args.get("kungfu")
        
        # 计算伤害
        damage, messages = self.calculator.calculate_damage(
            combatant.character,
            target.character,
            move,
            kungfu,
            self.context
        )
        
        try:
            with self.transaction() as txn:
                # 记录快照
                txn.snapshot(target.character, ['hp'])
                txn.snapshot(combatant.character, ['mp'])
                
                # 执行操作
                target.character.hp -= int(damage)
                if hasattr(combatant.character, 'mp'):
                    combatant.character.mp -= move.mp_cost
                
                # 提交（如果没有异常）
                txn.commit()
                
        except Exception as e:
            logger.exception("战斗操作失败")
            return False, f"操作失败: {e}"
        
        # 设置冷却
        cooldown = self._calculate_cooldown(combatant, move)
        combatant.set_cooldown(cooldown)
        
        # 构建消息
        msg = f"你对{target.character.name}使用{move.name}，造成{damage:.0f}点伤害！"
        if messages:
            msg += " " + " ".join(messages)
        
        return True, msg
```

### 2.3 测试用例

**文件**: `tests/unit/test_combat_transaction.py`

```python
import pytest
from unittest.mock import MagicMock

from src.game.combat.transaction import CombatTransaction


class TestCombatTransaction:
    """测试战斗事务"""
    
    def test_snapshot_and_rollback(self):
        """测试快照和回滚"""
        obj = MagicMock()
        obj.hp = 100
        obj.mp = 50
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp', 'mp'])
        
        # 修改对象
        obj.hp = 50
        obj.mp = 20
        
        # 回滚
        txn.rollback()
        
        # 验证恢复
        assert obj.hp == 100
        assert obj.mp == 50
    
    def test_commit_clears_snapshot(self):
        """测试提交后清除快照"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp'])
        
        obj.hp = 50
        txn.commit()
        
        # 提交后快照已清除，回滚无效
        txn.rollback()
        assert obj.hp == 50  # 未恢复
    
    def test_auto_rollback_on_exception(self):
        """测试异常时自动回滚"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        
        try:
            with txn.auto_rollback():
                txn.snapshot(obj, ['hp'])
                obj.hp = 50
                raise ValueError("模拟异常")
        except ValueError:
            pass
        
        # 验证已回滚
        assert obj.hp == 100
```

### 2.4 验证步骤

```bash
# 1. 运行新测试
python -m pytest tests/unit/test_combat_transaction.py -v

# 2. 运行战斗相关测试
python -m pytest tests/unit/test_combat*.py -v

# 3. 运行集成测试
python -m pytest tests/integration/ -v --tb=short

# 4. 手动验证（启动游戏进行战斗）
```

---

## 3. Mixin方法前缀规范实施

### 3.1 制定命名规范

**文件**: `docs/standards/mixin_naming.md`

```markdown
# Mixin命名规范

## 规则

1. **方法前缀**: 每个Mixin的所有公共方法必须添加前缀
2. **前缀格式**: `{mixin_name}_`
3. **统一接口**: Character类负责聚合各Mixin功能

## 当前Mixin前缀表

| Mixin | 前缀 | 示例 |
|:------|:-----|:-----|
| CharacterEquipmentMixin | `equipment_` | `equipment_get_stats` |
| CharacterWuxueMixin | `wuxue_` | `wuxue_get_available_moves` |

## 重命名清单

### CharacterEquipmentMixin

- [ ] `get_stats` → `equipment_get_stats`
- [ ] `get_equipped` → `equipment_get_equipped`
- [ ] `equip` → `equipment_equip`
- [ ] `unequip` → `equipment_unequip`
- [ ] `can_equip` → `equipment_can_equip`
- [ ] `get_total_stats` → `equipment_get_total_stats`
- [ ] `get_set_bonuses` → `equipment_get_set_bonuses`

### CharacterWuxueMixin

- [ ] `get_available_moves` → `wuxue_get_available_moves`
- [ ] `learn_wuxue` → `wuxue_learn`
- [ ] `has_learned` → `wuxue_has_learned`
- [ ] `get_wuxue_level` → `wuxue_get_level`
- [ ] `practice_move` → `wuxue_practice_move`
```

### 3.2 批量重命名脚本

**文件**: `tools/rename_mixin_methods.py`

```python
#!/usr/bin/env python3
"""批量重命名Mixin方法"""

import re
from pathlib import Path

REPLACEMENTS = [
    # CharacterEquipmentMixin
    (r'\.get_stats\(', '.equipment_get_stats('),
    (r'\.get_equipped\(', '.equipment_get_equipped('),
    (r'\.equip\(', '.equipment_equip('),
    (r'\.unequip\(', '.equipment_unequip('),
    
    # CharacterWuxueMixin
    (r'\.get_available_moves\(', '.wuxue_get_available_moves('),
    (r'\.learn_wuxue\(', '.wuxue_learn('),
    (r'\.has_learned\(', '.wuxue_has_learned('),
]

def rename_in_file(filepath: Path):
    """重命名文件中的方法调用"""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"Updated: {filepath}")

if __name__ == '__main__':
    src_dir = Path('src')
    test_dir = Path('tests')
    
    for py_file in list(src_dir.rglob('*.py')) + list(test_dir.rglob('*.py')):
        rename_in_file(py_file)
```

### 3.3 手动修改示例

**修改前** (`src/game/typeclasses/equipment.py`):

```python
class CharacterEquipmentMixin:
    def get_stats(self) -> dict[str, int]:
        """获取装备属性加成"""
        ...
    
    def get_equipped(self, slot: EquipmentSlot) -> Equipment | None:
        ...
```

**修改后**:

```python
class CharacterEquipmentMixin:
    def equipment_get_stats(self) -> dict[str, int]:
        """获取装备属性加成"""
        ...
    
    def equipment_get_equipped(self, slot: EquipmentSlot) -> Equipment | None:
        ...
```

### 3.4 Character统一接口

**修改** (`src/game/typeclasses/character.py`):

```python
class Character(CharacterEquipmentMixin, CharacterWuxueMixin, TypeclassBase):
    """武侠角色类型"""
    
    # ===== 统一属性接口 =====
    
    def get_attack(self) -> int:
        """获取总攻击力（聚合所有来源）"""
        base = self.attributes.get("strength", 10) * 2
        equipment = self.equipment_get_stats().get("attack", 0)
        wuxue = self.wuxue_get_stats().get("attack", 0)
        return base + equipment + wuxue
    
    def get_defense(self) -> int:
        """获取总防御力"""
        base = self.attributes.get("constitution", 10)
        equipment = self.equipment_get_stats().get("defense", 0)
        return base + equipment
    
    def get_stats(self) -> dict[str, int]:
        """获取所有属性（聚合）"""
        stats = {
            "strength": self.attributes.get("strength", 10),
            "agility": self.attributes.get("agility", 10),
            "constitution": self.attributes.get("constitution", 10),
        }
        stats.update(self.equipment_get_stats())
        stats.update(self.wuxue_get_stats())
        return stats
```

### 3.5 验证步骤

```bash
# 1. 运行所有测试
python -m pytest tests/ -v

# 2. 检查是否有遗漏的调用
python -c "
import subprocess
result = subprocess.run(['grep', '-r', '\.get_stats(', 'src/', '--include=*.py'], 
                       capture_output=True, text=True)
if result.stdout:
    print('找到未重命名的调用:')
    print(result.stdout)
"
```

---

## 4. 状态一致性检查实施

### 4.1 创建验证模块

**文件**: `src/game/typeclasses/validation.py`

```python
"""状态验证模块.

提供对象状态一致性检查和自动修复功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .character import Character


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    current_value: Any
    expected_range: str


class StateValidator:
    """状态验证器基类"""
    
    def __init__(self):
        self._rules: list[tuple[str, Callable[[Any], bool], str]] = []
    
    def add_rule(self, field: str, check: Callable[[Any], bool], message: str):
        """添加验证规则"""
        self._rules.append((field, check, message))
    
    def validate(self, obj: Any) -> list[ValidationError]:
        """验证对象状态"""
        errors = []
        for field, check, message in self._rules:
            value = getattr(obj, field, None)
            if not check(value):
                errors.append(ValidationError(
                    field=field,
                    message=message,
                    current_value=value,
                    expected_range="见验证规则"
                ))
        return errors


class CharacterValidator(StateValidator):
    """角色状态验证器"""
    
    def __init__(self):
        super().__init__()
        self._setup_rules()
    
    def _setup_rules(self):
        """设置角色验证规则"""
        # HP规则
        self.add_rule(
            'hp',
            lambda v: v is not None and v >= 0,
            'HP不能为负数'
        )
        
        # MP规则
        self.add_rule(
            'mp',
            lambda v: v is not None and v >= 0,
            'MP不能为负数'
        )
        
        # 等级规则
        self.add_rule(
            'level',
            lambda v: v is not None and 1 <= v <= 1000,
            '等级应在1-1000之间'
        )
    
    def validate(self, character: Character) -> list[ValidationError]:
        """验证角色状态"""
        errors = super().validate(character)
        
        # 额外检查
        if hasattr(character, 'hp') and hasattr(character, 'max_hp'):
            if character.hp > character.max_hp:
                errors.append(ValidationError(
                    field='hp',
                    message='HP超过上限',
                    current_value=character.hp,
                    expected_range=f'0-{character.max_hp}'
                ))
        
        return errors
    
    def fix(self, character: Character) -> list[str]:
        """自动修复状态问题"""
        fixes = []
        
        # 修复HP
        if hasattr(character, 'hp'):
            if character.hp < 0:
                character.hp = 0
                fixes.append('HP从负数修复为0')
            elif hasattr(character, 'max_hp') and character.hp > character.max_hp:
                character.hp = character.max_hp
                fixes.append(f'HP修复为上限{character.max_hp}')
        
        # 修复MP
        if hasattr(character, 'mp'):
            if character.mp < 0:
                character.mp = 0
                fixes.append('MP从负数修复为0')
            elif hasattr(character, 'max_mp') and character.mp > character.max_mp:
                character.mp = character.max_mp
                fixes.append(f'MP修复为上限{character.max_mp}')
        
        return fixes
```

### 4.2 集成到Character

**修改** (`src/game/typeclasses/character.py`):

```python
from .validation import CharacterValidator

class Character(...):
    def __init__(self, db_model):
        super().__init__(db_model)
        self._validator = CharacterValidator()
    
    def validate_state(self) -> list[str]:
        """验证状态一致性，返回错误列表"""
        errors = self._validator.validate(self)
        return [f"[{e.field}] {e.message}: 当前={e.current_value}" for e in errors]
    
    def fix_state(self) -> list[str]:
        """自动修复状态问题"""
        return self._validator.fix(self)
    
    def is_state_valid(self) -> bool:
        """检查状态是否有效"""
        return len(self.validate_state()) == 0
```

### 4.3 调试命令

**文件**: `src/game/commands/debug.py`

```python
"""调试命令"""

from src.engine.commands.command import Command


class CmdValidateCharacter(Command):
    """验证角色状态"""
    key = "@validate_character"
    aliases = ["@vc"]
    locks = "perm(Admin)"
    
    async def execute(self):
        if not self.args:
            self.caller.msg("用法: @validate_character <角色ID>")
            return
        
        try:
            char_id = int(self.args)
        except ValueError:
            self.caller.msg("角色ID必须是数字")
            return
        
        # 获取角色
        from src.engine.objects.manager import ObjectManager
        manager = ObjectManager()
        character = manager.get(char_id)
        
        if not character:
            self.caller.msg(f"找不到角色: {char_id}")
            return
        
        # 验证状态
        errors = character.validate_state()
        
        if not errors:
            self.caller.msg(f"角色 {character.name} 状态正常")
        else:
            self.caller.msg(f"角色 {character.name} 状态异常:")
            for error in errors:
                self.caller.msg(f"  - {error}")
            
            # 询问是否修复
            fixes = character.fix_state()
            if fixes:
                self.caller.msg("已自动修复:")
                for fix in fixes:
                    self.caller.msg(f"  - {fix}")
```

### 4.4 定期自动检查

```python
# 在游戏循环中添加定期检查
async def _periodic_state_check(self):
    """定期状态检查"""
    if self.engine.tick % 600 == 0:  # 每10分钟
        for character in self.engine.objects.get_all_characters():
            if not character.is_state_valid():
                logger.warning(f"角色 {character.name} 状态异常，自动修复")
                character.fix_state()
```

---

## 5. 战斗策略模式重构实施

（因篇幅限制，后续章节略。完整手册包含所有Phase的详细实施步骤）

---

## 9. 测试规范

### 9.1 单元测试要求

```python
# 每个改进必须附带测试
class TestNewFeature:
    """测试新功能"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.reset_state()
    
    def teardown_method(self):
        """每个测试后执行"""
        self.cleanup()
    
    def test_normal_case(self):
        """测试正常情况"""
        pass
    
    def test_edge_case(self):
        """测试边界情况"""
        pass
    
    def test_error_case(self):
        """测试异常情况"""
        pass
```

### 9.2 集成测试要求

```python
# 测试模块间协作
@pytest.mark.asyncio
async def test_integration():
    """测试集成"""
    engine = await create_test_engine()
    
    # 执行操作
    result = await engine.process_command(...)
    
    # 验证结果
    assert result.success
    assert result.data == expected
```

### 9.3 回归测试清单

- [ ] 所有原有战斗功能正常
- [ ] 角色属性计算正确
- [ ] 物品系统正常
- [ ] 任务系统正常
- [ ] NPC行为正常
- [ ] 存档/读档正常

---

## 10. 故障排除

### 10.1 常见问题

#### 问题1: 事务回滚不生效

**症状**: 异常后状态未恢复

**检查**:
1. 确认`snapshot()`在修改前调用
2. 确认`rollback()`被调用
3. 检查对象引用是否正确

#### 问题2: Mixin方法冲突

**症状**: 调用方法时行为异常

**检查**:
1. 查看MRO: `print(Character.__mro__)`
2. 确认方法前缀正确
3. 检查是否有重复定义

#### 问题3: 循环导入错误

**症状**: `ImportError`或运行时错误

**解决**:
1. 使用`TYPE_CHECKING`延迟导入
2. 将导入移到函数内部
3. 重构模块结构

### 10.2 回滚策略

如果改进导致严重问题，快速回滚:

```bash
# 方法1: 使用备份分支
git checkout backup/pre-architecture-improvement

# 方法2: 使用tag
git checkout v1.0-pre-improvement

# 方法3: 撤销特定提交
git revert <commit-hash>
```

---

## 附录

### A. 代码审查清单

- [ ] 代码符合PEP 8规范
- [ ] 有适当的文档字符串
- [ ] 有类型提示
- [ ] 有错误处理
- [ ] 有测试覆盖
- [ ] 不影响现有功能

### B. 提交规范

```
type(scope): subject

body

footer
```

示例:
```
refactor(combat): 添加事务保护机制

- 实现CombatTransaction类
- 集成到CombatSession
- 添加自动回滚支持

Closes #123
```

---

*实施手册完成: 2026-02-23*

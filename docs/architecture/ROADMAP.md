# 金庸武侠MUD架构改进路线图

**版本**: 1.0  
**日期**: 2026-02-23  
**适用对象**: 单机版金庸武侠MUD  
**核心原则**: 稳定性 > 可扩展性 > 可维护性 > 健壮性

---

## 路线图概览

```
2026年Q1                            2026年Q2
─────────────────────────────────────────────────────────────────────
1月          2月          3月          4月          5月          6月
│            │            │            │            │            │
├─ Phase 1 ──┤            ├─ Phase 2 ──┤            ├─ Phase 3 ──┤
│ 紧急修复   │            │ 架构改进   │            │ 可选优化   │
│ (4-6周)    │            │ (8-10周)   │            │ (持续)     │
│            │            │            │            │            │
└────────────┴────────────┴────────────┴────────────┴────────────┘

Phase 1: 紧急修复
├── Week 1-2: 战斗系统事务保护
├── Week 3-4: Mixin方法前缀规范
└── Week 5-6: 状态一致性检查

Phase 2: 架构改进
├── Month 1: 战斗策略模式重构
├── Month 2: 循环依赖解耦 + 组件模式试点
└── Month 3: 配置外置化

Phase 3: 可选优化
├── ECS架构探索
├── 领域事件系统（如需要）
└── 高级调试工具
```

---

## Phase 1: 紧急修复（4-6周）

### 目标
解决影响稳定性的核心问题，防止数据不一致和运行时崩溃。

### Week 1-2: 战斗系统事务保护

#### 任务清单

| 任务 | 负责人 | 预计工时 | 依赖 |
|:-----|:------|:--------|:-----|
| T1.1: 设计CombatTransaction类 | - | 4h | 无 |
| T1.2: 实现状态快照机制 | - | 6h | T1.1 |
| T1.3: 实现回滚机制 | - | 6h | T1.2 |
| T1.4: 集成到CombatSession | - | 8h | T1.3 |
| T1.5: 编写单元测试 | - | 8h | T1.4 |
| T1.6: 回归测试 | - | 4h | T1.5 |

#### 交付物
- `src/game/combat/transaction.py` - 事务保护模块
- `tests/unit/test_combat_transaction.py` - 测试用例
- 更新后的 `src/game/combat/core.py`

#### 验收标准
```python
# 所有战斗操作应使用事务保护
with self.transaction() as txn:
    target.hp -= damage
    attacker.mp -= mp_cost
    txn.commit()  # 原子提交
    
# 异常时自动回滚
try:
    with self.transaction() as txn:
        target.hp -= damage
        raise Exception("模拟异常")
        txn.commit()
except Exception:
    pass
# 断言: target.hp 应恢复到操作前
```

### Week 3-4: Mixin方法前缀规范

#### 任务清单

| 任务 | 负责人 | 预计工时 | 依赖 |
|:-----|:------|:--------|:-----|
| T2.1: 梳理所有Mixin方法 | - | 4h | 无 |
| T2.2: 制定命名规范 | - | 2h | T2.1 |
| T2.3: 重命名EquipmentMixin方法 | - | 6h | T2.2 |
| T2.4: 重命名WuxueMixin方法 | - | 6h | T2.2 |
| T2.5: 更新Character统一接口 | - | 4h | T2.3, T2.4 |
| T2.6: 更新所有调用点 | - | 8h | T2.5 |
| T2.7: 测试验证 | - | 4h | T2.6 |

#### 命名规范
```python
# EquipmentMixin 方法前缀: equipment_
class CharacterEquipmentMixin:
    def equipment_get_stats(self) -> dict: ...
    def equipment_get_attack(self) -> int: ...
    def equipment_get_defense(self) -> int: ...
    def equipment_can_equip(self, item) -> bool: ...

# WuxueMixin 方法前缀: wuxue_
class CharacterWuxueMixin:
    def wuxue_get_stats(self) -> dict: ...
    def wuxue_get_available_moves(self) -> list: ...
    def wuxue_can_learn(self, kungfu) -> bool: ...

# Character 统一暴露接口
class Character(...):
    def get_attack(self) -> int:
        return (
            self.equipment_get_attack() + 
            self.wuxue_get_attack_bonus() +
            self.attributes.get("strength", 0) * 2
        )
```

#### 交付物
- 更新后的 `src/game/typeclasses/equipment.py`
- 更新后的 `src/game/typeclasses/wuxue.py`
- 更新后的 `src/game/typeclasses/character.py`
- 命名规范文档 `docs/standards/mixin_naming.md`

### Week 5-6: 状态一致性检查

#### 任务清单

| 任务 | 负责人 | 预计工时 | 依赖 |
|:-----|:------|:--------|:-----|
| T3.1: 设计状态验证接口 | - | 4h | 无 |
| T3.2: 实现Character.validate_state | - | 6h | T3.1 |
| T3.3: 实现Character.fix_state | - | 4h | T3.2 |
| T3.4: 添加调试命令 @validate | - | 4h | T3.3 |
| T3.5: 定期自动检查机制 | - | 4h | T3.3 |
| T3.6: 测试用例 | - | 6h | T3.4 |

#### 交付物
- `src/game/typeclasses/validation.py` - 状态验证模块
- 更新后的 `src/game/typeclasses/character.py`
- 调试命令 `@validate_character`
- 测试用例

#### 验收标准
```python
char = Character(db_model)
char.hp = -100  # 无效状态
char.mp = 9999  # 超过上限

errors = char.validate_state()
assert len(errors) == 2
assert "HP为负" in errors[0]
assert "MP超过上限" in errors[1]

char.fix_state()  # 自动修复
assert char.hp == 0
assert char.mp == char.max_mp
assert len(char.validate_state()) == 0
```

---

## Phase 2: 架构改进（8-10周）

### Month 1: 战斗策略模式重构

#### 目标
将战斗行动从硬编码改为策略模式，支持插件化扩展。

#### 任务分解

**Week 1-2: 基础框架**
```python
# src/game/combat/strategy.py
class CombatActionStrategy(ABC):
    @abstractmethod
    async def execute(self, session, combatant, args) -> ActionResult: ...
    
    @abstractmethod
    def validate(self, session, combatant, args) -> tuple[bool, str]: ...
    
    @abstractmethod
    def get_cooldown(self) -> float: ...
    
    @abstractmethod
    def get_mp_cost(self) -> int: ...

class ActionResult:
    success: bool
    message: str
    side_effects: list  # 记录副作用，用于回滚
```

**Week 3-4: 迁移现有行动**
- AttackStrategy
- CastStrategy
- FleeStrategy
- DefendStrategy

**Week 5-6: 集成与测试**
- 修改CombatSession使用策略模式
- 确保100%向后兼容
- 编写策略模式测试

#### 交付物
- `src/game/combat/strategy.py` - 策略基类
- `src/game/combat/strategies/` - 具体策略实现
- 更新后的 `src/game/combat/core.py`
- 策略模式文档

#### 验收标准
```python
# 新增行动类型无需修改CombatSession
class CustomStrategy(CombatActionStrategy):
    async def execute(self, session, combatant, args):
        # 自定义逻辑
        ...

session.register_action("custom", CustomStrategy())
result = await session.execute_action(combatant, "custom", args)
```

### Month 2: 循环依赖解耦 + 组件模式试点

#### Week 1-2: 循环依赖分析
- 绘制完整依赖图
- 识别关键依赖点
- 制定解耦计划

#### Week 3-4: 依赖注入实现
```python
# 改造示例
class BehaviorTree:
    def __init__(self, 
                 npc: NPC,
                 movement_service: MovementService,
                 combat_checker: CombatChecker):
        self.npc = npc
        self.movement = movement_service
        self.combat = combat_checker
```

#### Week 5-6: 组件模式试点
选择一个新功能使用组件模式实现：
```python
# 示例：宠物系统使用组件模式
class PetComponent(Component):
    def __init__(self, owner: Character):
        super().__init__(owner)
        self.loyalty = 100
        self.level = 1
    
    def get_stats(self) -> dict:
        return {"pet_attack": self.level * 5}

# 使用
char.add_component("pet", PetComponent(char))
pet_stats = char.get_component("pet").get_stats()
```

### Month 3: 配置外置化

#### 任务清单
- 将游戏平衡参数移至YAML配置
- 实现配置热加载
- 添加配置验证

#### 交付物
- `data/balance.yml` - 游戏平衡配置
- `data/factions.yml` - 门派配置
- `src/utils/config_loader.py` - 配置加载器

#### 示例配置
```yaml
# data/balance.yml
combat:
  damage:
    base: 10
    variance: 0.1
    crit_chance: 0.1
    counter_bonus: 0.2
  
  cooldown:
    base: 3.0
    min: 1.0
    agility_factor: 0.02

leveling:
  exp_curve: [100, 200, 400, 800, 1600]
  hp_per_level: 25
  mp_per_level: 15

factions:
  thresholds:
    hostile: -2000
    unfriendly: -500
    neutral: 0
    friendly: 500
    respected: 2000
    revered: 5000
```

---

## Phase 3: 可选优化（持续）

### ECS架构探索

**目标**: 评估ECS架构是否适合项目长期发展

**探索内容**:
1. ECS原型实现
2. 与现有架构对比测试
3. 迁移成本评估

**决策点**: 3个月后决定是否全面迁移

### 领域事件系统

**触发条件**: 当需要以下功能时
- 任务自动追踪
- 成就系统
- 统计系统
- 战斗回放

**实现方案**:
```python
# src/utils/event_bus.py
class EventBus:
    def subscribe(self, event_type: str, handler: callable): ...
    def publish(self, event: DomainEvent): ...
```

### 高级调试工具

#### 功能列表
- `@inspect_character <id>` - 查看角色完整状态
- `@inspect_combat <id>` - 查看战斗会话状态
- `@trace <on/off>` - 开启/关闭调用追踪
- `@validate_all` - 验证所有对象状态

#### 实现优先级
1. P1: inspect_character
2. P2: validate_all
3. P3: trace
4. P4: inspect_combat

---

## 资源规划

### 人力资源

| 阶段 | 需要技能 | 建议人数 | 预计工时 |
|:-----|:---------|:--------:|:--------|
| Phase 1 | Python, 熟悉现有代码 | 1-2人 | 120-180h |
| Phase 2 | Python, 设计模式 | 1-2人 | 240-300h |
| Phase 3 | Python, 架构设计 | 1人 | 按需 |

### 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|:-----|:------:|:----:|:---------|
| 重构引入新bug | 高 | 高 | 完善的测试覆盖，渐进式重构 |
| 进度延期 | 中 | 中 | 分阶段交付，及时调整计划 |
| 与现有代码冲突 | 中 | 中 | 频繁集成，及时解决冲突 |
| 性能下降 | 低 | 中 | 性能基准测试，及时优化 |

### 质量保证

**每个Phase的交付标准**:
1. 代码审查通过
2. 单元测试覆盖率 > 80%
3. 集成测试全部通过
4. 回归测试无新bug
5. 文档同步更新

---

## 附录

### A. 术语表

| 术语 | 说明 |
|:-----|:-----|
| Mixin | 一种多重继承模式，提供特定功能 |
| MRO | Method Resolution Order，方法解析顺序 |
| ECS | Entity-Component-System架构 |
| 事务保护 | 保证一组操作原子性执行的机制 |
| 策略模式 | 定义算法族，分别封装起来，让它们可以互相替换 |

### B. 参考文档

- `IMPLEMENTATION_GUIDE.md` - 详细实施手册
- `ARCHITECTURE_ANALYSIS.md` - 架构分析报告
- `docs/standards/` - 编码规范

### C. 变更记录

| 版本 | 日期 | 变更内容 |
|:-----|:-----|:---------|
| 1.0 | 2026-02-23 | 初始版本 |

---

*路线图完成: 2026-02-23*

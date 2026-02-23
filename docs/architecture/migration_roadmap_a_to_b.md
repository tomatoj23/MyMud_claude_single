# 方案 A → 方案 B 渐进式过渡路线图

> 安全、可控、可回滚的 `name` 属性迁移计划

**版本**: v1.0  
**制定日期**: 2026-02-23  
**风险等级**: 低风险（通过分阶段控制）  
**预计总工期**: 2-3天（含观察期）

---

## 目录

- [执行摘要](#执行摘要)
- [阶段 0：准备与防护](#阶段-0准备与防护)
- [阶段 1：核心功能（方案A）](#阶段-1核心功能方案a)
- [阶段 2：观察与验证](#阶段-2观察与验证)
- [阶段 3：P1 优先级功能](#阶段-3p1-优先级功能)
- [阶段 4：观察与验证](#阶段-4观察与验证)
- [阶段 5：P2 优先级功能](#阶段-5p2-优先级功能)
- [阶段 6：最终验证与文档](#阶段-6最终验证与文档)
- [应急预案](#应急预案)
- [检查清单汇总](#检查清单汇总)

---

## 执行摘要

### 路线图概览

```
阶段0: 准备（建立安全网）
    │
    ▼ 安全网就绪
阶段1: 方案A（核心功能）
    │
    ▼ 测试通过
阶段2: 观察期（24小时）
    │
    ▼ 无异常报告
阶段3: P1功能（房间/装备/命令）
    │
    ▼ 测试通过
阶段4: 观察期（24小时）
    │
    ▼ 无异常报告
阶段5: P2功能（物品/NPC）
    │
    ▼ 测试通过
阶段6: 最终验证与文档
    │
    ▼ 完成
   结束
```

### 关键安全原则

| 原则 | 说明 |
|:---|:---|
| **永不破坏主分支** | 所有修改在 feature 分支完成 |
| **每阶段可独立回滚** | 每个阶段结束后打 tag，可单独回滚 |
| **测试不通过不前进** | 1329个测试必须全部通过才能进入下一阶段 |
| **观察期不跳过** | 即使测试通过，也必须经过观察期 |
| **数据安全第一** | 任何修改不得破坏现有存档数据 |

---

## 阶段 0：准备与防护

### 目标
建立完整的安全网，确保后续阶段可以安全回滚。

### 前置条件
- [ ] 当前工作目录干净（无未提交修改）
- [ ] 所有 1329 个测试通过
- [ ] 已推送最新代码到 GitHub

### 执行步骤

#### 步骤 0.1：创建功能分支

```bash
# 确保在主分支且最新
git checkout master
git pull origin master

# 创建功能分支
git checkout -b feature/name-attribute-migration

# 推送分支到远程
git push -u origin feature/name-attribute-migration
```

**验证**: 
```bash
git branch --show-current  # 应显示 feature/name-attribute-migration
```

---

#### 步骤 0.2：建立基线 Tag

```bash
# 打基线标签（阶段0完成）
git tag -a v1.0.0-baseline -m "name属性迁移基线 - 阶段0完成"
git push origin v1.0.0-baseline
```

**作用**: 如果需要完全回滚，可以回到这个状态。

---

#### 步骤 0.3：创建迁移跟踪文档

在项目中创建 `MIGRATION_LOG.md`：

```markdown
# 迁移跟踪日志

## 阶段 0：准备（完成）
- 时间: 2026-02-23
- 分支: feature/name-attribute-migration
- 基线 Tag: v1.0.0-baseline
- 状态: ✅ 完成

## 阶段 1：核心功能（进行中）
- 计划时间: 
- 实际时间:
- 修改文件:
- 测试状态:
- 问题记录:
- 状态: ⏳ 进行中
```

---

#### 步骤 0.4：预演数据兼容性测试

创建临时测试脚本 `test_data_compat.py`：

```python
"""验证数据兼容性 - 阶段0预演"""
import asyncio
from src.engine.core.engine import create_engine

async def test_backward_compatibility():
    """测试旧数据（无name）兼容性"""
    engine = create_engine()
    await engine.initialize()
    
    # 模拟旧数据（无name）
    old_npc = await engine.objects.create(
        typeclass_path="src.game.npc.core.NPC",
        key="old_npc_001",
        attributes={
            "npc_type": "merchant"
            # 注意：没有 name
        }
    )
    
    # 验证：应该能用 key 作为回退
    display_name = old_npc.name or old_npc.key
    assert display_name == "old_npc_001", f"期望 key，得到 {display_name}"
    print(f"✅ 旧数据兼容测试通过: {display_name}")
    
    # 模拟新数据（有name）
    new_npc = await engine.objects.create(
        typeclass_path="src.game.npc.core.NPC",
        key="new_npc_001",
        attributes={
            "name": "王铁匠",
            "npc_type": "merchant"
        }
    )
    
    # 验证：应该能用 name
    display_name = new_npc.name or new_npc.key
    assert display_name == "王铁匠", f"期望 name，得到 {display_name}"
    print(f"✅ 新数据测试通过: {display_name}")
    
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(test_backward_compatibility())
```

**执行**:
```bash
python test_data_compat.py
```

**预期输出**:
```
✅ 旧数据兼容测试通过: old_npc_001
✅ 新数据测试通过: 王铁匠
```

---

#### 步骤 0.5：备份当前数据库（如有生产数据）

```bash
# 如果有生产数据库，备份
cp data/game.db data/game.db.baseline.$(date +%Y%m%d)
```

---

### 阶段 0 验证清单

- [ ] 功能分支已创建并推送
- [ ] 基线 Tag 已打并推送
- [ ] 迁移日志已创建
- [ ] 数据兼容性测试通过
- [ ] 当前所有 1329 个测试通过

### 阶段 0 完成标记

```bash
# 提交阶段0文档
git add MIGRATION_LOG.md test_data_compat.py
git commit -m "chore: 阶段0完成 - 迁移准备工作

- 创建功能分支 feature/name-attribute-migration
- 建立基线标签 v1.0.0-baseline
- 创建迁移跟踪日志
- 数据兼容性预演测试通过
- 备份生产数据"
```

---

## 阶段 1：核心功能（方案A）

### 目标
实现方案 A：添加 `name` 属性，修改战斗系统。

### 前置条件
- [ ] 阶段 0 已完成
- [ ] 在功能分支上工作

### 执行步骤

#### 步骤 1.1：添加 `name` 属性到 Character

**文件**: `src/game/typeclasses/character.py`

**修改**（在之前规划的属性位置添加）:

```python
@property
def name(self) -> str:
    """
    角色显示名称。
    
    返回 attributes 中的 name，如果不存在则返回 key。
    这确保向后兼容：旧对象没有 name 时显示 key。
    
    Returns:
        显示名称（name 或 key 回退）
    """
    return self.db.get("name") or self.key

@name.setter
def name(self, value: str) -> None:
    """
    设置角色显示名称。
    
    Args:
        value: 显示名称
    """
    self.db.set("name", value)
```

**验证**:
```bash
python -c "from src.game.typeclasses.character import Character; print('✅ Character 导入成功')"
```

---

#### 步骤 1.2：修改战斗系统

**文件**: `src/game/combat/core.py`

**修改 5 处**（如之前规划）:

```python
# 第 261 行
msg = f"你对{target.name}使用「{move.name}」，" if result.is_hit else "你使用招式但未命中，"

# 第 271 行  
msg = f"你攻击{target.name}，造成 {damage} 点伤害！"

# 第 345 行
self._log(f"{combatant.character.name} 使用了物品")

# 第 365 行
msg = f"{combatant.character.name} 使用「{move.name if move else '普通攻击'}」"

# 第 368 行
msg += f" 对 {target.name} 造成 {int(result.damage)} 点伤害！"

# 第 370 行
msg = f"{combatant.character.name} 的攻击被 {target.name} 闪开了！"
```

---

#### 步骤 1.3：添加 `name` 属性测试

**文件**: `tests/unit/test_character.py`

在文件中添加：

```python
class TestCharacterName:
    """Character name 属性测试"""
    
    def test_name_defaults_to_key(self, mock_manager, mock_db_model):
        """测试 name 默认值回退到 key"""
        char = Character(mock_manager, mock_db_model)
        # 没有设置 name，应该返回 key
        assert char.name == char.key
    
    def test_name_custom_value(self, mock_manager, mock_db_model):
        """测试自定义 name"""
        char = Character(mock_manager, mock_db_model)
        char.name = "王铁匠"
        assert char.name == "王铁匠"
        assert char.key != "王铁匠"  # key 不变
    
    def test_name_empty_string_fallback(self, mock_manager, mock_db_model):
        """测试空字符串回退到 key"""
        char = Character(mock_manager, mock_db_model)
        char.db.set("name", "")  # 设置空字符串
        assert char.name == char.key  # 应该回退到 key
    
    def test_name_persistence(self, mock_manager, mock_db_model):
        """测试 name 持久化到 attributes"""
        char = Character(mock_manager, mock_db_model)
        char.name = "测试名称"
        # 验证存储在 db 中
        assert char.db.get("name") == "测试名称"
```

---

#### 步骤 1.4：更新战斗测试

**文件**: `tests/unit/test_combat_core_coverage.py`

**修改**（第 669 行附近）:

```python
# 当前
assert f"{enemy_char.key} 使用了物品" in session.log
# 改为
assert f"{enemy_char.name} 使用了物品" in session.log
```

注意：需要确保 mock 对象有 `name` 属性：

```python
@pytest.fixture
def enemy_char():
    char = Mock()
    char.id = 2
    char.key = "enemy"
    char.name = "敌人"  # 添加 name
    char.get_hp.return_value = (100, 100)
    char.is_alive = True
    return char
```

---

#### 步骤 1.5：全面测试

```bash
# 运行所有测试
python -m pytest tests/ -v --tb=short

# 特别关注
python -m pytest tests/unit/test_character.py -v
python -m pytest tests/unit/test_combat.py -v
python -m pytest tests/unit/test_combat_core_coverage.py -v
```

**必须通过**: 1329/1329 测试

---

### 阶段 1 验证清单

- [ ] `name` 属性添加成功
- [ ] 战斗系统 5 处修改完成
- [ ] Character 的 `name` 测试添加并通过
- [ ] 战斗测试更新并通过
- [ ] **所有 1329 个测试通过**

### 阶段 1 完成标记

```bash
# 更新迁移日志
git add -A
git commit -m "feat: 阶段1完成 - 添加name属性和战斗系统修改

- Character 添加 name 属性（默认回退到 key）
- 战斗系统 5 处修改使用 name
- 添加 name 属性单元测试
- 更新战斗测试断言
- 所有 1329 个测试通过

下一步: 阶段2观察期"

# 打阶段1标签
git tag -a v1.1.0-phase1 -m "阶段1完成 - 核心功能"
git push origin v1.1.0-phase1
```

---

## 阶段 2：观察与验证

### 目标
观察阶段 1 修改在生产环境（或模拟环境）中的表现。

### 持续时间
**24 小时**（最少，建议 48 小时）

### 观察指标

#### 2.1 功能正确性

运行完整游戏流程测试：

```bash
python -m pytest tests/integration/test_phase2_game_systems.py::TestCrossSystemIntegration::test_full_combat_scenario -v
```

**预期**: 战斗日志显示 `name`（如 "王铁匠"）而非 `key`（如 "npc_001"）

#### 2.2 数据兼容性

```bash
python test_data_compat.py
```

**预期**: 旧对象显示 `key`，新对象显示 `name`

#### 2.3 性能指标

```bash
python -m pytest benchmarks/test_core_performance.py -v
```

**预期**: 无性能退化（与基线对比 < 5% 差异）

---

### 观察期检查清单（每小时检查一次，共 24 次）

| 时间 | 检查项 | 结果 | 签名 |
|:---:|:---|:---:|:---:|
| 0h | 所有测试通过 | ⬜ | |
| 0h | 数据兼容测试通过 | ⬜ | |
| 6h | 无错误日志 | ⬜ | |
| 12h | 无异常报告 | ⬜ | |
| 24h | 决定进入阶段3 | ⬜ | |

### 阶段 2 进入条件

必须全部满足：
- [ ] 24 小时内无测试失败
- [ ] 无错误日志报告
- [ ] 无性能退化
- [ ] 手动验证战斗显示正确

### 阶段 2 问题处理

| 问题级别 | 处理方式 |
|:---|:---|
| 测试失败 | 修复后重新进入阶段 2（重置 24 小时计时） |
| 性能退化 > 10% | 回滚到阶段 1，分析原因 |
| 数据显示异常 | 立即回滚到阶段 0，紧急修复 |

---

## 阶段 3：P1 优先级功能

### 目标
实现房间、装备、命令的 `name` 显示。

### 包含修改

| 文件 | 修改数 | 影响 |
|:---|:---:|:---|
| `room.py` | 4处 | 场景描述 |
| `equipment.py` | 3处 | 装备操作反馈 |
| `default.py` | 5处 | 命令输出 |

### 执行策略

**分批次修改，每批次验证**：

#### 批次 3.1：房间显示

```bash
# 修改 room.py 4 处
# 提交
git add src/game/typeclasses/room.py
git commit -m "feat: 房间显示使用 name"

# 测试
python -m pytest tests/integration/test_phase2_game_systems.py::TestMapSystemFlow -v
```

#### 批次 3.2：装备显示

```bash
# 修改 equipment.py 3 处
# 提交
git add src/game/typeclasses/equipment.py
git commit -m "feat: 装备显示使用 name"

# 测试
python -m pytest tests/integration/test_phase2_game_systems.py::TestEquipmentSystemFlow -v
```

#### 批次 3.3：命令输出

```bash
# 修改 default.py 5 处
# 提交
git add src/engine/commands/default.py
git commit -m "feat: 命令输出使用 name"

# 测试
python -m pytest tests/unit/test_default_commands.py -v
```

### 阶段 3 验证清单

- [ ] 房间描述显示 `name`
- [ ] 装备操作显示 `name`
- [ ] 命令输出显示 `name`
- [ ] **所有 1329 个测试通过**

### 阶段 3 完成标记

```bash
git tag -a v1.2.0-phase3 -m "阶段3完成 - P1功能"
git push origin v1.2.0-phase3
```

---

## 阶段 4：观察与验证

同阶段 2，持续 24 小时。

**重点观察**:
- 房间描述是否正确
- 装备操作反馈是否友好
- 命令输出是否一致

---

## 阶段 5：P2 优先级功能

### 目标
实现物品、NPC 对话的 `name` 显示。

### 包含修改

| 文件 | 修改数 | 影响 |
|:---|:---:|:---|
| `item.py` | 1处 | 物品描述 |
| `npc/core.py` | 1处 | 对话回退 |

### 阶段 5 验证清单

- [ ] 物品描述显示 `name`
- [ ] NPC 对话回退逻辑正确
- [ ] **所有 1329 个测试通过**

### 阶段 5 完成标记

```bash
git tag -a v1.3.0-phase5 -m "阶段5完成 - P2功能"
git push origin v1.3.0-phase5
```

---

## 阶段 6：最终验证与文档

### 目标
完成全部迁移，合并到主分支。

### 执行步骤

#### 步骤 6.1：最终全面测试

```bash
# 完整测试套件
python -m pytest tests/ -v --cov=src --cov-report=html

# 性能基准
python -m pytest benchmarks/ -v

# 数据兼容
python test_data_compat.py
```

**必须**: 覆盖率不下降，性能不退化

---

#### 步骤 6.2：更新文档

更新以下文档：
- [ ] `docs/api/game_api.md` - 添加 `name` 属性说明
- [ ] `MIGRATION_LOG.md` - 记录完整迁移过程
- [ ] `TODO.md` - 标记任务完成

---

#### 步骤 6.3：代码审查清单

- [ ] 所有修改使用 `name or key` 模式
- [ ] 无硬编码字符串
- [ ] 文档字符串完整
- [ ] 测试覆盖新增代码

---

#### 步骤 6.4：合并到主分支

```bash
# 确保功能分支最新
git checkout feature/name-attribute-migration
git pull origin master  # 合并主分支最新变更

# 解决可能的冲突
# 再次运行测试
python -m pytest tests/

# 合并到主分支
git checkout master
git merge --no-ff feature/name-attribute-migration -m "feat: 完成name属性迁移（方案A→B）

渐进式迁移完成：
- 阶段0: 准备与防护
- 阶段1: 核心功能（方案A）
- 阶段2: 观察验证
- 阶段3: P1功能（房间/装备/命令）
- 阶段4: 观察验证
- 阶段5: P2功能（物品/NPC）
- 阶段6: 最终验证

所有1329个测试通过，无性能退化。"

# 推送
git push origin master

# 最终标签
git tag -a v2.0.0-name-migration -m "name属性迁移完成"
git push origin v2.0.0-name-migration
```

---

## 应急预案

### 场景 1：阶段中发现严重 Bug

```bash
# 立即回滚到上一阶段
git checkout v1.1.0-phase1  # 或相应标签

# 修复 Bug
# ...

# 重新进入当前阶段（重置计时器）
```

### 场景 2：阶段 3/5 中测试失败

**不回滚，只修复当前阶段**:

```bash
# 在当前阶段修复
git add -A
git commit -m "fix: 修复阶段X中的问题"

# 重新运行测试
python -m pytest tests/

# 测试通过后，继续观察期（重置24小时计时）
```

### 场景 3：需要完全放弃迁移

```bash
# 回滚到基线
git checkout master
git reset --hard v1.0.0-baseline

# 删除功能分支
git branch -D feature/name-attribute-migration
git push origin --delete feature/name-attribute-migration

# 清理标签（可选）
git tag -d v1.1.0-phase1 v1.2.0-phase3 v1.3.0-phase5
```

---

## 检查清单汇总

### 前置条件（必须全部满足）

- [ ] 所有 1329 个测试当前通过
- [ ] 工作目录干净
- [ ] 已备份生产数据
- [ ] 有充足时间（3天）

### 每阶段必做

- [ ] 代码修改完成
- [ ] 测试添加/更新
- [ ] 1329 个测试通过
- [ ] 数据兼容测试通过
- [ ] 性能基准无退化
- [ ] 提交并打标签
- [ ] 更新迁移日志

### 观察期必做

- [ ] 24 小时无测试失败
- [ ] 无错误日志
- [ ] 手动验证通过
- [ ] 决定进入下一阶段

---

## 时间线总览

| 阶段 | 预计时间 | 实际时间 | 状态 |
|:---:|:---:|:---:|:---:|
| 0: 准备 | 2h | | ⏳ 待开始 |
| 1: 核心功能 | 4h | | ⏳ 待开始 |
| 2: 观察期 | 24h | | ⏳ 待开始 |
| 3: P1功能 | 4h | | ⏳ 待开始 |
| 4: 观察期 | 24h | | ⏳ 待开始 |
| 5: P2功能 | 2h | | ⏳ 待开始 |
| 6: 最终验证 | 2h | | ⏳ 待开始 |
| **总计** | **~62h (2.5天)** | | |

---

## 批准签名

迁移负责人确认：

| 阶段 | 计划时间 | 实际完成 | 负责人签名 | 备注 |
|:---:|:---:|:---:|:---:|:---|
| 0 | | | | |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |

---

**此计划确保**: 
- ✅ 每个阶段可独立回滚
- ✅ 每步都有验证标准
- ✅ 数据安全优先
- ✅ 渐进式风险可控

**您确认后，我将开始执行阶段 0。**

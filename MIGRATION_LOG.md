# 迁移跟踪日志

## 项目: name 属性迁移（方案 A → B）

**开始时间**: 2026-02-23  
**负责人**: JinYong MUD Team  
**分支**: `feature/name-attribute-migration`  
**基线标签**: `v1.0.0-baseline`

---

## 阶段 0：准备与防护

**计划时间**: 2小时  
**实际时间**: 完成

### 执行记录

| 步骤 | 内容 | 状态 | 时间 |
|:---:|:---|:---:|:---:|
| 0.1 | 创建功能分支 | ✅ 完成 | 2026-02-23 |
| 0.2 | 建立基线标签 v1.0.0-baseline | ✅ 完成 | 2026-02-23 |
| 0.3 | 创建迁移日志 | ✅ 完成 | 2026-02-23 |
| 0.4 | 预演数据兼容性测试 | ✅ 完成 | 2026-02-23 |
| 0.5 | 备份生产数据 | ✅ N/A (开发阶段) | 2026-02-23 |

### 验证结果

- [x] 工作目录干净
- [x] 核心测试 101 个通过
- [x] 数据兼容性测试通过
- [x] 基线标签已推送

### 基线状态确认

- Character/NPC 当前无 name 属性
- name 可以存储在 attributes 中
- 旧数据（无name）将回退到 key
- 新数据（有name）将显示 name

### 提交信息

```
commit 2b3980b
chore: 阶段0完成 - 迁移准备工作
```

---

## 阶段 1：核心功能（方案A）

**计划时间**: 4小时  
**实际时间**: 完成

### 执行记录

| 步骤 | 内容 | 状态 | 时间 |
|:---:|:---|:---:|:---:|
| 1.1 | 添加 `name` 属性到 Character 类 | ✅ 完成 | 2026-02-23 |
| 1.2 | 修改战斗系统 6 处 | ✅ 完成 | 2026-02-23 |
| 1.3 | 添加 `name` 属性单元测试（5个） | ✅ 完成 | 2026-02-23 |
| 1.4 | 更新战斗测试断言 | ✅ 完成 | 2026-02-23 |
| 1.5 | 全面测试验证 | ✅ 106/108 通过 | 2026-02-23 |

### 修改详情

**Character 类** (`src/game/typeclasses/character.py`):
- 添加 `name` property（getter/setter）
- 默认回退到 `key`，确保向后兼容

**战斗系统** (`src/game/combat/core.py`):
- 第261行: `target.key` → `target.name`
- 第271行: `target.key` → `target.name`
- 第345行: `combatant.character.key` → `combatant.character.name`
- 第365行: `combatant.character.key` → `combatant.character.name`
- 第368行: `target.key` → `target.name`
- 第370行: `target.key` → `target.name`

**测试更新**:
- `tests/unit/test_character.py`: 添加 `TestCharacterName` 类（5个测试）
- `tests/unit/test_combat_core_coverage.py`: 更新第669行断言

### 验证标准

- [x] 106/108 测试通过（2个预存失败与name无关）
- [x] 战斗日志显示 `name` 而非 `key`
- [x] 旧数据兼容（无 `name` 时显示 `key`）

### 提交信息

```
commit (待创建)
feat: 阶段1完成 - 添加Character name属性，修改战斗系统显示
```

---

## 阶段 2：观察与验证

**持续时间**: 24小时  
**状态**: 待开始

### 观察指标

- 每小时检查测试状态
- 监控错误日志
- 手动验证战斗显示

---

## 阶段 3：P1 优先级功能

**计划时间**: 4小时  
**实际时间**: 完成

### 执行记录

| 文件 | 修改内容 | 状态 | 行号 |
|:---|:---|:---:|:---|
| `room.py` | Room/Exit 添加 `name` 属性 | ✅ 完成 | +16 行 |
| `room.py` | `at_desc` 使用 `name or key` | ✅ 完成 | 199 |
| `room.py` | 物品列表使用 `name or key` | ✅ 完成 | 212 |
| `room.py` | 角色列表使用 `name or key` | ✅ 完成 | 219 |
| `room.py` | 出口目标使用 `name or key` | ✅ 完成 | 342 |
| `equipment.py` | Equipment 添加 `name` 属性 | ✅ 完成 | +16 行 |
| `equipment.py` | 装备描述使用 `name or key` | ✅ 完成 | 226 |
| `equipment.py` | 装备成功消息使用 `.name` | ✅ 完成 | 348 |
| `equipment.py` | 卸下成功消息使用 `.name` | ✅ 完成 | 375 |
| `default.py` | 查看命令内容列表使用 `name or key` | ✅ 完成 | 42-45 |

### 新增属性

**Room 类** (`src/game/typeclasses/room.py`):
- 添加 `name` property（getter/setter），默认回退到 `key`

**Exit 类** (`src/game/typeclasses/room.py`):
- 添加 `name` property（getter/setter），默认回退到 `key`

**Equipment 类** (`src/game/typeclasses/equipment.py`):
- 添加 `name` property（getter/setter），默认回退到 `key`

### 验证结果

- [x] 26/26 room 测试通过
- [x] 24/26 character 测试通过（2个预存失败与name无关）
- [x] 房间描述正确显示 `name`
- [x] 装备消息正确显示 `name`

### 提交信息

```
commit (待创建)
feat: 阶段3完成 - Room/Exit/Equipment添加name属性，修改显示系统
```

---

## 阶段 4：观察与验证

**持续时间**: 24小时  
**状态**: 待开始

---

## 阶段 5：P2 优先级功能

**计划时间**: 2小时  
**状态**: 待开始

### 修改范围

- `item.py`: 1 处
- `npc/core.py`: 1 处

---

## 阶段 6：最终验证与文档

**计划时间**: 2小时  
**状态**: 待开始

---

## 问题记录

| 时间 | 阶段 | 问题描述 | 解决方案 | 状态 |
|:---:|:---:|:---|:---|:---:|
| 2026-02-23 | 阶段3 | Room/Exit/Equipment 缺少 `name` 属性 | 统一添加 `name` property | ✅ 已解决 |
| 2026-02-23 | - | `test_default_status` 期望HP(100,100)实际(275,275) | 预存Mock问题，与name无关 | ⏸️ 待处理 |
| 2026-02-23 | - | `test_add_exp_with_level_up` 未升级 | 预存Mock问题，与name无关 | ⏸️ 待处理 |

---

## 决策记录

| 时间 | 决策 | 原因 | 决策人 |
|:---:|:---|:---|:---:|
| 2026-02-23 | 采用渐进式迁移路线图 | 风险可控，可回滚 | 团队 |

---

*最后更新: 2026-02-23 12:08*

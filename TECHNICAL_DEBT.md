# 技术债务报告

> 金庸武侠MUD项目技术债务追踪

**生成日期**: 2026-02-23  
**更新日期**: 2026-02-23  

---

## 📊 债务概览

| 类别 | 总数 | 已完成 | 剩余 | 优先级 |
|:---|:---:|:---:|:---:|:---:|
| 架构债务 | 14 | 10 | 4 | 见架构债务文档 |
| 功能债务 (TODO) | 34 | 1 | 33 | P1:1, P2:26, P3:6 |
| **总计** | **48** | **11** | **37** | - |

---

## ✅ 已清偿债务 (11项)

### 架构债务 (10项)
- [x] **ARCH-001** 单例模式状态污染
- [x] **ARCH-002** 异步代码同步调用风险
- [x] **ARCH-003** ~~战斗系统属性名不一致~~ (路径分隔符问题)
- [x] **ARCH-004** 测试覆盖率不足 (新增52个测试)
- [x] **ARCH-005** 魔法字符串→枚举定义
- [x] **ARCH-006** 循环导入风险→协议接口
- [x] **ARCH-007** 异常处理体系完善
- [x] **ARCH-008** 资源清理机制完善
- [x] **ARCH-009** 输入验证加强
- [x] **ARCH-010** 代码文档规范
- [x] **ARCH-011** 测试代码重复消除

### 功能债务 (1项)
- [x] **TD-014/TODO-028** 负重检查系统 (`item.py`)

---

## 🔴 高优先级债务 (P1)

### 1. 命令系统未实现方法
**文件**: `src/engine/commands/command.py:110`  
**问题**: `execute()` 抽象方法  
**说明**: 模板方法模式，子类必须实现

```python
def execute(self) -> CommandResult:
    raise NotImplementedError(f"命令 {self.key} 未实现 execute 方法")
```

---

## 🟡 中优先级债务 (P2) - 26项

### NPC系统 (14项)

| ID | 文件 | 行号 | 功能描述 |
|:---:|:---|:---:|:---|
| TD-002 | npc/behavior_tree.py | 219 | 移动到巡逻点 |
| TD-003 | npc/behavior_tree.py | 238 | 检查与出生点距离 |
| TD-004 | npc/behavior_tree.py | 259 | 随机移动逻辑 |
| TD-005 | npc/behavior_tree.py | 270 | 检查是否在战斗中 |
| TD-006 | npc/behavior_tree.py | 281 | 获取游戏时间 |
| TD-007 | npc/behavior_tree.py | 293 | 检查范围内玩家 |
| TD-008 | npc/behavior_tree.py | 313 | 检查离家距离 |
| TD-009 | npc/reputation.py | 257 | 派系关系系统 |
| TD-010 | npc/dialogue.py | 281 | 检查背包 |
| TD-011 | npc/dialogue.py | 318 | 给予物品 |
| TD-012 | npc/dialogue.py | 341 | 解锁任务 |
| TD-013 | npc/dialogue.py | 356 | 记录世界状态 |

### 核心系统 (12项)

| ID | 文件 | 功能 |
|:---:|:---|:---|
| TD-015 | room.py:348 | 出口锁系统 |
| TD-016 | equipment.py:417 | 套装效果计算 |
| TD-017 | wuxue.py:298 | 武学缓存 |
| TD-018 | command.py:85 | 命令锁检查 |
| TD-019 | handler.py:85 | 动态命令集合 |
| TD-020 | quest/core.py:346 | 任务物品发放 |
| TD-021 | quest/core.py:351 | 武学奖励 |
| TD-022 | combat/core.py:169 | 实时战斗结算 |
| TD-023 | combat/core.py:283 | 内功施法 |
| TD-024 | calculator.py:95 | 防御者武学类型 |
| TD-025 | calculator.py:154 | 招式命中修正 |
| TD-026/027 | ai.py | AI克制/属性选择 |

---

## 🟢 低优先级债务 (P3) - 6项

| ID | 文件 | 问题 |
|:---:|:---|:---|
| - | main_window.py | GUI未完成方法 (setup_menus/closeEvent) |
| - | backends.py | 事件调度后端抽象方法 |
| - | test_character.py | Mock问题导致2个测试失败 |
| ARCH-012 | object/manager.py | 性能优化空间 |
| ARCH-013 | 多处 | 类型注解不完善 |
| ARCH-014 | object/manager.py | 缓存无过期策略 |

---

## 📈 债务分布

### 按模块
```
npc/          14 项 (41%)  ← 最需关注
combat/        7 项 (21%)
typeclasses/   5 项 (15%)
commands/      4 项 (12%)
quest/         2 项 (6%)
```

### 按类型
```
AI/行为        9 项 (26%)
系统功能       8 项 (24%)
计算/公式      6 项 (18%)
检查/验证      5 项 (15%)
```

---

## 🎯 清偿路线图

### 近期 (本周)
1. **TD-015** 出口锁系统 - 地图核心功能
2. **TD-016** 套装效果 - 装备核心功能

### 中期 (2-4周)
3. **NPC AI行为树** (TD-002~008) - 让世界更生动
4. **战斗计算完善** (TD-022~027)

### 长期 (可选)
5. **派系关系** (TD-009)
6. **任务奖励** (TD-020/021)

---

## 📚 相关文档

| 文档 | 内容 | 位置 |
|:---|:---|:---|
| `ARCHITECTURE_DEBT.md` | 架构债务详情 | `docs/architecture/` |
| `TECHNICAL_DEBT.md` | 功能债务总览 | 本文件 |

---

*最后更新: 2026-02-23*

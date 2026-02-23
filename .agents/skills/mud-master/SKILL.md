---
name: mud-master
description: 金庸武侠MUD项目完整开发助手，整合架构规划、代码编写、代码审查三大功能。支持完整的开发工作流：阶段规划→代码生成→代码审查→循环迭代，直至验收通过。在MUD项目开发全流程中调用。
---

# MUD项目开发大师

## 功能概述

本 Skill 是《金庸武侠文字MUD》项目的**一站式开发助手**，整合了：

1. **架构规划** - 六阶段开发路线图、模块分解、验收标准
2. **代码编写** - 完整代码模板、技术规范、实现指南
3. **代码审查** - 详细检查清单、性能指标、问题分级

支持**全自动开发工作流**，无需手动切换 Skill。

## 三种工作模式

### 模式一：完整工作流（推荐）

一句话启动完整开发循环：

```
用户：启动阶段一，实现项目骨架模块

→ 自动读取阶段规划
→ 自动生成代码
→ 自动审查代码
→ 输出审查报告和修复建议
→ 如未通过，自动修复并重审
→ 通过后标记完成，询问是否继续下一模块
```

### 模式二：分步执行

按需执行单个步骤：

```
用户：@mud-master 规划阶段二
用户：@mud-master 生成 Character 类代码
用户：@mud-master 审查这段代码
```

### 模式三：交互式开发

逐步引导用户完成开发：

```
用户：开始开发

→ 询问当前阶段
→ 列出该阶段模块
→ 让用户选择要实现的模块
→ 生成代码
→ 询问是否立即审查
→ ...
```

## 核心工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    完整开发循环                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  1.规划  │───→│  2.编码  │───→│  3.审查  │             │
│  │          │    │          │    │          │             │
│  │ 读取阶段 │    │ 选用模板 │    │ 检查清单 │             │
│  │ 分解模块 │    │ 生成代码 │    │ 运行测试 │             │
│  │ 明确规范 │    │ 自检语法 │    │ 输出报告 │             │
│  └──────────┘    └──────────┘    └────┬─────┘             │
│       ↑                                 │                   │
│       │         ┌─────────────┐         │ 通过              │
│       └─────────┤   循环迭代  │←────────┘                   │
│                 │  (自动修复) │                             │
│                 └──────┬──────┘                             │
│                        │ 通过                                │
│                        ↓                                    │
│                 ┌─────────────┐                             │
│                 │  标记完成   │                             │
│                 │ 进入下一模块│                             │
│                 └─────────────┘                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 开发阶段总览

| 阶段 | 名称 | 主要内容 | 预计工期 |
|:---|:---|:---|:---|
| **阶段一** | 引擎核心搭建 | Typeclass、ObjectManager、Command、EventScheduler、GameEngine | 第1-3周 |
| **阶段二** | 武侠世界构建 | Character、装备、武学、地图 | 第4-5周 |
| **阶段三** | 玩法系统实现 | 战斗、任务、NPC、自然语言 | 第6-7周 |
| **阶段四** | GUI客户端 | PySide6、面板、主题 | 第8周 |
| **阶段五** | 内容制作 | 世界数据、武学数据、任务、NPC | 第9-15周 |
| **阶段六** | 存档系统 | 存档、开发者模式、平衡测试 | 第16-17周 |

## 详细参考

### 阶段规划

| 文档 | 内容 |
|:---|:---|
| [references/phase1.md](references/phase1.md) | 阶段一：引擎核心搭建 |
| [references/phase2.md](references/phase2.md) | 阶段二：武侠世界构建 |
| [references/phase3.md](references/phase3.md) | 阶段三：玩法系统实现 |
| [references/phase4.md](references/phase4.md) | 阶段四：GUI客户端 |
| [references/phase5.md](references/phase5.md) | 阶段五：内容制作与集成 |
| [references/phase6.md](references/phase6.md) | 阶段六：存档与系统功能 |

### 代码模板

#### 核心系统

| 文档 | 内容 | 用途 |
|:---|:---|:---|
| [references/templates.md](references/templates.md) | 基础组件模板 | AttributeHandler、Command等 |
| [references/typeclass.md](references/typeclass.md) | Typeclass系统 | 动态类、属性代理 |
| [references/commands.md](references/commands.md) | Command系统 | 命令解析、CmdSet |
| [references/scheduler.md](references/scheduler.md) | EventScheduler | 事件调度 |
| [references/engine.md](references/engine.md) | GameEngine | 核心整合 |
| [references/save.md](references/save.md) | 存档系统 | 序列化、自动存档 |

#### 游戏内容

| 文档 | 内容 | 用途 |
|:---|:---|:---|
| [references/character.md](references/character.md) | 角色系统 | 属性、门派、内力 |
| [references/equipment.md](references/equipment.md) | 装备系统 | 槽位、套装、耐久 |
| [references/wuxue.md](references/wuxue.md) | 武学系统 | 武功、招式、克制 |
| [references/world.md](references/world.md) | 地图系统 | 房间、出口、寻路 |
| [references/combat.md](references/combat.md) | 战斗系统 | 回合制、BUFF、AI |
| [references/quest_npc.md](references/quest_npc.md) | 任务与NPC | 任务链、行为树、对话 |

#### GUI与项目基础

| 文档 | 内容 | 用途 |
|:---|:---|:---|
| [references/gui.md](references/gui.md) | GUI系统 | PySide6、面板、主题 |
| [references/message_bus.md](references/message_bus.md) | 消息总线系统 | 引擎与GUI通信 |
| [references/project_skeleton.md](references/project_skeleton.md) | 项目骨架 | 目录、配置、日志 |

#### 测试与质量保证

| 文档 | 内容 | 用途 |
|:---|:---|:---|
| [references/chaos_testing.md](references/chaos_testing.md) | 混沌测试方法论 | 异常行为测试 |
| [references/tests.md](references/tests.md) | 测试模板 | 单元测试和集成测试 |

### 审查清单

| 文档 | 内容 |
|:---|:---|
| [references/checklists.md](references/checklists.md) | 各系统详细审查清单 |
| [references/tests.md](references/tests.md) | 单元测试和集成测试模板 |
| [references/acceptance.md](references/acceptance.md) | 六阶段验收标准 |

## 使用示例

### 示例1：完整工作流（一句话开发）

```
用户：启动阶段一，实现Typeclass动态类系统

mud-master:
  ═══════════════════════════════════════════════════
  启动完整开发循环
  ═══════════════════════════════════════════════════
  
  [步骤1/3] 规划阶段
  ├── 阶段：阶段一 - 引擎核心搭建
  ├── 模块：Typeclass动态类系统
  ├── 依赖：ORM模型（需先完成）
  └── 规范：见 phase1.md 1.2.3
  
  [步骤2/3] 生成代码
  ├── 读取 typeclass.md
  ├── 生成 TypeclassBase 类
  ├── 生成 AttributeHandler 类
  ├── 生成 TypeclassLoader 类
  └── 输出：src/engine/core/typeclass.py
  
  [步骤3/3] 代码审查
  ├── [✓] 架构符合性
  ├── [✓] 代码质量
  ├── [!] 功能测试 - 缺少单元测试
  └── 结论：有条件通过
  
  ═══════════════════════════════════════════════════
  审查结果：有条件通过
  ═══════════════════════════════════════════════════
  
  问题清单：
  | 级别 | 问题 | 建议 |
  | 警告 | 缺少单元测试 | 参考 tests.md 补充测试 |
  
  建议操作：
  1. 补充单元测试（可选）
  2. 标记模块完成，进入下一模块
  
  请选择：补充测试 / 继续下一模块 / 修复其他问题
```

### 示例2：仅生成代码

```
用户：生成EventScheduler的代码

mud-master:
  → 读取 references/scheduler.md
  → 根据模板生成完整代码
  → 输出代码文件
  → 提示：生成完成，使用"审查这段代码"进行质量检查
```

### 示例3：仅审查代码

```
用户：审查以下代码 [粘贴代码]

mud-master:
  → 读取 references/checklists.md
  → 逐项检查
  → 输出审查报告
  → 如发现问题，提供修复建议
```

### 示例4：阶段规划

```
用户：阶段二有哪些模块？

mud-master:
  → 读取 references/phase2.md
  → 输出阶段二模块清单和依赖关系
  → 建议执行顺序
```

## 输出规范

### 完整工作流输出格式

```markdown
═══════════════════════════════════════════════════
[步骤X/3] 步骤名称
═══════════════════════════════════════════════════

[内容...]

═══════════════════════════════════════════════════
审查结果：[通过/有条件通过/不通过]
═══════════════════════════════════════════════════

## 问题清单（如有）
| 级别 | 位置 | 问题 | 建议修复 |
|:---|:---|:---|:---|
| 严重 | file.py:42 | xxx | yyy |

## 建议操作
1. [操作1]
2. [操作2]
```

### 单独代码生成输出格式

```markdown
## 实现摘要
- 实现模块: xxx
- 代码文件数: n
- 关键类/函数: [列表]

## 代码文件

### src/xxx/yyy.py
```python
[完整代码]
```

## 依赖检查
- [x] 依赖的模块已实现
- [x] 无循环依赖
- [x] 类型注解完整

## 自测结果
- [x] 语法检查通过
- [x] 基本导入测试通过
- [x] 代码风格检查通过
```

## 技术栈要求

| 组件 | 必须使用 | 禁止使用 |
|:---|:---|:---|
| 数据库 | SQLite + SQLAlchemy 2.0 | Django ORM |
| 异步 | asyncio + async/await | Twisted |
| GUI | PySide6 + qasync | PyQt5 |
| 序列化 | MessagePack | Pickle |

## 问题分级标准

| 级别 | 定义 | 处理方式 |
|:---|:---|:---|
| **阻塞** | 导致系统无法运行 | 必须修复 |
| **严重** | 功能缺陷/性能问题 | 必须修复 |
| **警告** | 代码异味 | 建议修复 |
| **建议** | 风格优化 | 可选 |

## 性能指标

| 指标 | 目标值 |
|:---|:---|
| 命令响应时间 | < 100ms |
| 内存占用 | < 500MB |
| 启动时间 | < 5秒 |
| 单场景对象数 | 100+ |

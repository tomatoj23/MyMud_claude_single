---
name: mud-coder
description: 金庸武侠MUD项目代码编写助手。提供Python代码模板、开发规范检查、代码生成指导，用于MUD游戏引擎的Typeclass系统、Command系统、EventScheduler等核心模块开发。在编写MUD项目代码时调用。
---

# MUD代码编写助手

## 功能概述

本 Skill 提供《金庸武侠文字MUD》项目开发所需的：

1. **代码模板** - 各类组件的标准代码模板
2. **开发规范** - 项目强制的技术栈和代码风格
3. **实现指南** - 核心系统的实现要点

## 使用场景

- 创建新的 Typeclass、Command、系统模块
- 查阅项目技术规范确保代码符合要求
- 获取标准代码模板快速开始开发

## 技术栈强制要求

| 组件 | 必须使用 | 禁止使用 |
|:---|:---|:---|
| 数据库 | SQLite + SQLAlchemy 2.0 | Django ORM, PostgreSQL |
| 异步 | asyncio + async/await | Twisted, 线程池 |
| GUI | PySide6 + qasync | PyQt5, Kivy |
| 序列化 | MessagePack | Pickle（不安全） |
| 配置 | YAML/JSON | INI, XML |

## 代码质量标准

**必须做到：**
- Python 3.11+ 类型注解完整（函数参数、返回值、类属性）
- 使用 `async/await` 处理异步逻辑，禁止混用回调
- 遵循Black格式（行宽100）
- 所有公共API有Google Style Docstring
- 错误处理使用异常而非返回码

**禁止事项：**
- 使用 `Any` 类型（除非必要且有说明）
- 遗留 `TODO` 或 `FIXME` 不处理
- 使用全局可变状态
- 阻塞异步事件循环的同步操作

## 详细参考

### 核心系统

| 文档 | 内容 | 何时使用 |
|:---|:---|:---|
| [templates.md](references/templates.md) | 各类组件的代码模板 | 需要创建新组件时 |
| [typeclass.md](references/typeclass.md) | Typeclass系统实现指南 | 实现/修改Typeclass时 |
| [commands.md](references/commands.md) | Command系统实现指南 | 实现/修改Command时 |
| [scheduler.md](references/scheduler.md) | EventScheduler实现指南 | 实现事件调度时 |
| [engine.md](references/engine.md) | GameEngine核心整合 | 实现引擎整合时 |
| [save.md](references/save.md) | 存档系统 | 实现存档功能时 |

### 游戏内容

| 文档 | 内容 | 何时使用 |
|:---|:---|:---|
| [character.md](references/character.md) | 角色系统 | 实现角色属性/门派/内力时 |
| [equipment.md](references/equipment.md) | 装备系统 | 实现装备槽位/属性加成时 |
| [wuxue.md](references/wuxue.md) | 武学系统 | 实现武功/招式/克制时 |
| [world.md](references/world.md) | 地图系统 | 实现房间/出口/寻路时 |
| [combat.md](references/combat.md) | 战斗系统 | 实现战斗/BUFF/AI时 |
| [quest_npc.md](references/quest_npc.md) | 任务与NPC系统 | 实现任务/行为树/对话时 |

### GUI系统

| 文档 | 内容 | 何时使用 |
|:---|:---|:---|
| [gui.md](references/gui.md) | GUI面板与主题 | 实现PySide6界面时 |

### 项目基础

| 文档 | 内容 | 何时使用 |
|:---|:---|:---|
| [project_skeleton.md](references/project_skeleton.md) | 项目骨架与配置 | 初始化项目时 |

## 输出规范

编写代码时，响应应包含：

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
- [ ] 依赖的模块已实现
- [ ] 无循环依赖
- [ ] 类型注解完整

## 自测结果
- [ ] 语法检查通过
- [ ] 基本导入测试通过
- [ ] 代码风格检查通过
```

## 阶段对应速查表

| 阶段 | 主要工作 | 需要查阅的文档 |
|:---|:---|:---|
| **阶段一** | 引擎核心 | `typeclass.md`, `commands.md`, `scheduler.md`, `engine.md` |
| **阶段二** | 武侠世界 | `character.md`, `equipment.md`, `wuxue.md`, `world.md` |
| **阶段三** | 玩法系统 | `combat.md`, `quest_npc.md` |
| **阶段四** | GUI客户端 | `gui.md` |
| **阶段五** | 内容制作 | `world.md` (YAML数据格式), `wuxue.md` (武学数据) |
| **阶段六** | 存档系统 | `save.md`, `gui.md` (开发者模式) |
| **初始化** | 项目搭建 | `project_skeleton.md`, `templates.md` |

## 示例：创建 AttributeHandler

```
用户：创建 AttributeHandler 类

→ 读取 references/templates.md 中的 AttributeHandler 模板
→ 根据 typeclass.md 指南编写完整代码
→ 按输出规范格式返回
```

## 示例：实现装备系统

```
用户：实现装备系统

→ 读取 references/equipment.md 了解装备系统设计
→ 参考其中 Equipment 类和 EquipmentSlot 定义
→ 创建 CharacterEquipmentMixin 混入 Character
→ 按输出规范返回代码
```

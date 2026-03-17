# 文档目录

> 金庸武侠MUD项目的完整文档库

---

## 📚 文档导航

### 入门指南

| 文档 | 说明 |
|:---|:---|
| [快速开始](./guides/quickstart.md) | 环境搭建、第一个游戏对象、基础教程 |
| [开发规范](./guides/coding_standards.md) | 代码风格、Git规范、测试规范 |
| [项目根目录README](../README.md) | 项目概览和基本信息 |

### API文档

| 文档 | 说明 |
|:---|:---|
| [核心引擎API](./api/core_api.md) | GameEngine、TypeclassBase、ObjectManager等核心API |
| [游戏系统API](./api/game_api.md) | Character、Combat、Quest、NPC等游戏系统API |

### 架构文档

| 文档 | 说明 |
|:---|:---|
| [架构概述](./architecture/overview.md) | 系统架构、设计模式、模块依赖 |
| [数据流文档](./architecture/data_flow.md) | 玩家输入、对象创建、战斗流程等数据流 |
| [技术债务分析](./architecture/tech_debt_analysis.md) | 代码质量分析、债务跟踪、改进建议 |
| [name属性迁移规划](./architecture/name_attribute_migration_plan.md) | 为Character添加name属性的详细规划 |
| [迁移路线图A→B](./architecture/migration_roadmap_a_to_b.md) | 方案A到方案B的渐进式过渡路线图 |

### 性能与设计

| 文档 | 说明 |
|:---|:---|
| [性能优化设计](./performance_optimization_design.md) | 性能优化架构设计 |
| [性能优化实现](./performance_optimizations.md) | 性能优化具体实现 |
| [性能监控设计](./architecture/PERFORMANCE_MONITORING_DESIGN.md) | 运行时性能监控方案（S3）|

### 项目规划

| 文档 | 说明 |
|:---|:---|
| [技术债务报告](./tech_debt_report.md) | 技术债务清偿报告（2026-02-26更新）|
| [当前项目规格说明](./specs/current_project_spec.md) | 当前阶段的统一规格基线（2026-03-11） |
| [Phase 4 GUI 子规格说明](./specs/phase4_gui_spec.md) | GUI 阶段的执行规格与验收基线（2026-03-11） |
| [Phase 4 GUI 执行任务清单](./specs/phase4_gui_task_list.md) | GUI 阶段的实施顺序与任务拆解（2026-03-11） |
| [开发计划](../DEVELOPMENT_PLAN.md) | 详细开发路线图 |
| [任务清单](../TODO.md) | 当前开发任务状态 |
| [迁移日志](../MIGRATION_LOG.md) | 功能迁移和架构改进记录 |
| [技术实现研究](../单机版金庸武侠文字MUD技术实现与游戏设计研究.md) | 技术选型和游戏设计研究 |

### 规范与标准

| 文档 | 说明 |
|:---|:---|
| [Mixin命名规范](./standards/mixin_naming.md) | Mixin方法命名规范 |

---

## 快速链接

### 按角色查找

**新开发者**
1. [快速开始](./guides/quickstart.md)
2. [开发规范](./guides/coding_standards.md)
3. [架构概述](./architecture/overview.md)

**API使用者**
1. [核心引擎API](./api/core_api.md)
2. [游戏系统API](./api/game_api.md)

**架构师/维护者**
1. [架构概述](./architecture/overview.md)
2. [数据流文档](./architecture/data_flow.md)
3. [技术债务分析](./architecture/tech_debt_analysis.md)

---

### 归档文档

以下文档已归档，供历史参考：

| 文档 | 说明 | 归档位置 |
|:---|:---|:---|
| 架构分析报告 | Phase 1/2/3架构分析 | `docs/architecture/archive/analysis/` |
| 实施手册 | 架构改进实施指南 | `docs/architecture/archive/guides/` |
| 路线图 | 架构改进路线图 | `docs/architecture/archive/planning/` |
| 债务详细清单 | 技术债务详细分析 | `docs/architecture/archive/` |
| 测试报告 | 历史测试报告 | `docs/archive/test_reports/` |
| 工作流程 | 架构改进工作流 | `docs/archive/workflow/` |

---

## 文档状态

| 文档 | 状态 | 最后更新 |
|:---|:---:|:---:|
| 快速开始 | ✅ 完整 | 2026-02-23 |
| 开发规范 | ✅ 完整 | 2026-02-23 |
| 核心引擎API | ✅ 完整 | 2026-02-23 |
| 游戏系统API | ✅ 完整 | 2026-02-23 |
| 架构概述 | ✅ 完整 | 2026-02-23 |
| 数据流文档 | ✅ 完整 | 2026-02-23 |
| 技术债务分析 | ✅ 完整 | 2026-02-23 |
| 性能监控设计 | ✅ 完整 | 2026-02-26 |
| 技术债务报告 | ✅ 完整 | 2026-02-26 |
| 当前项目规格说明 | ✅ 完整 | 2026-03-11 |
| Phase 4 GUI 子规格说明 | ✅ 完整 | 2026-03-11 |
| Phase 4 GUI 执行任务清单 | ✅ 完整 | 2026-03-11 |

---

## 贡献文档

### 文档规范

1. 使用 Markdown 格式
2. 代码块标注语言类型
3. 图表使用 ASCII 或 Mermaid
4. 保持中英文混排时空格

### 更新流程

1. 修改相关文档
2. 更新本文档的状态表
3. 提交到Git仓库
4. 推送至GitHub

---

*最后更新: 2026-03-11*

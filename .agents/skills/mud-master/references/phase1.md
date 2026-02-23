# 阶段一：引擎核心搭建（第1-3周）

## 阶段目标

构建完整的MUD引擎核心，包括对象系统、命令系统、事件系统等基础设施。

## 模块清单

| 顺序 | 模块 | 依赖 | 状态 |
|:---|:---|:---|:---|
| 1 | 项目骨架（目录、配置、日志） | 无 | 待开始 |
| 2 | SQLite数据库基础设施 | 1 | 待开始 |
| 3 | ORM模型与实体基类 | 2 | 待开始 |
| 4 | Typeclass动态类系统 | 3 | 待开始 |
| 5 | ObjectManager对象管理器 | 4 | 待开始 |
| 6 | CmdSet命令集合系统 | 5 | 待开始 |
| 7 | 命令解析流水线 | 6 | 待开始 |
| 8 | EventScheduler事件调度 | 7 | 待开始 |
| 9 | GameEngine整合 | 8 | 待开始 |
| 10 | 基础命令实现 | 9 | 待开始 |

## 详细模块说明

### 模块1：项目骨架
- 创建标准Python项目目录结构
- 配置pyproject.toml、日志系统
- 初始化Git仓库和.gitignore

### 模块2：SQLite数据库基础设施
- 数据库连接管理
- 迁移系统基础
- 连接池配置

### 模块3：ORM模型与实体基类
- SQLAlchemy 2.0 模型基类
- 通用的Object模型（id, key, typeclass_path, location等）

### 模块4：Typeclass动态类系统
- AttributeHandler 属性代理
- 动态类加载（importlib）
- 生命周期钩子（at_init, at_delete, at_move）

### 模块5：ObjectManager对象管理器
- L1缓存（weakref）
- L2缓存（lru_cache）
- 批量保存机制
- find()查询方法

### 模块6：CmdSet命令集合系统
- Command基类（key, aliases, locks）
- CmdSet集合类
- 优先级合并机制

### 模块7：命令解析流水线
- 输入预处理
- Trie树前缀匹配
- 权限锁检查
- 命令执行

### 模块8：EventScheduler事件调度
- asyncio实现的调度器
- 延迟/周期/条件/帧事件支持
- 优先级队列（heapq）
- 时间膨胀控制

### 模块9：GameEngine整合
- 各子系统整合
- 启动/关闭流程
- 主事件循环

### 模块10：基础命令实现
- look（查看）
- goto/enter（移动）
- create（创建对象）
- inventory（背包）

## 阶段验收标准

- [ ] 可通过命令行与引擎交互
- [ ] 支持创建对象、移动、查看等基本操作
- [ ] 事件调度器可正确处理延迟/周期任务
- [ ] 对象修改后正确标记dirty并持久化

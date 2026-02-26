# 工作流程文档

**用途**: 记录如何使用架构分析文档进行改进工作  
**更新日期**: 2026-02-23  
**配套文档**: ARCHITECTURE_ANALYSIS.md, ROADMAP.md, IMPLEMENTATION_GUIDE.md

---

## 每天工作流程

### Step 1: 阅读 ARCHITECTURE_ANALYSIS.md（理解问题）

**做什么**:
- 了解每个问题的详细分析
- 理解问题与需求的映射关系
- 查看改进方案设计

**何时做**: 开始新任务前
**预计时间**: 15-30分钟

---

### Step 2: 阅读 ROADMAP.md（确定优先级）

**做什么**:
- 确定改进优先级
- 了解时间安排
- 评估资源需求

**何时做**: 每周开始时
**预计时间**: 10-15分钟

---

### Step 3: 参考 IMPLEMENTATION_GUIDE.md（实施改进）

**做什么**:
- 按步骤实施
- 复制代码示例
- 遵循测试规范

**何时做**: 编码时
**预计时间**: 根据任务4-8小时

---

## 本次改进流程（Phase 1）

### 本周目标
战斗系统事务保护

### 具体步骤

**周一**: 
1. 阅读 ARCHITECTURE_ANALYSIS.md 第5章
2. 阅读 ROADMAP.md Phase 1
3. 准备开发环境
4. 开始 T1.1: 设计CombatTransaction类

**周二-周三**:
1. 参考 IMPLEMENTATION_GUIDE.md 第2章
2. 完成 T1.2-T1.4: 实现事务保护

**周四**:
1. 编写单元测试
2. 回归测试验证

**周五**:
1. 代码审查
2. 文档更新
3. 提交代码

---

## 快速参考

| 想做什么 | 看哪个文档 | 看哪章 |
|:---------|:-----------|:-------|
| 理解为什么要改 | ARCHITECTURE_ANALYSIS.md | 第2章（问题映射） |
| 了解方案设计 | ARCHITECTURE_ANALYSIS.md | 第3-6章（问题详解） |
| 确定优先级 | ROADMAP.md | 第7章（优化建议） |
| 了解时间安排 | ROADMAP.md | Phase 1/2/3 |
| 知道具体怎么做 | IMPLEMENTATION_GUIDE.md | 对应章节 |
| 复制代码 | IMPLEMENTATION_GUIDE.md | 代码示例 |
| 写测试 | IMPLEMENTATION_GUIDE.md | 第9章（测试规范） |
| 遇到问题 | IMPLEMENTATION_GUIDE.md | 第10章（故障排除） |

---

## 检查清单

### 开始工作前
- [ ] 阅读 ARCHITECTURE_ANALYSIS.md 相关章节
- [ ] 阅读 ROADMAP.md 确认优先级
- [ ] 参考 IMPLEMENTATION_GUIDE.md 了解实施步骤

### 编码时
- [ ] 按步骤实施，不跳过步骤
- [ ] 复制代码示例，根据实际调整
- [ ] 遵循测试规范，每个功能有测试

### 提交前
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档同步更新

---

## 示例

**今天要做**: 战斗系统事务保护

**步骤**:
```
1. 打开 ARCHITECTURE_ANALYSIS.md
   阅读: 5. 战斗系统紧耦合问题详解
   了解: 为什么要做、方案设计

2. 打开 ROADMAP.md
   阅读: Phase 1, Week 1-2
   确认: 任务清单和时间安排

3. 打开 IMPLEMENTATION_GUIDE.md
   阅读: 2. 战斗系统事务保护实施
   执行: 按T1.1-T1.6步骤实施
   复制: 代码示例到项目
   遵循: 测试规范编写测试
```

---

*工作流程文档完成*

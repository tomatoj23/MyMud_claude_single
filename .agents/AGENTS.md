# 金庸武侠MUD - Skill配置

## 项目级Skill

本项目使用自定义 Skill 支持开发：

| Skill | 路径 | 用途 | 推荐度 |
|:---|:---|:---|:---|
| **mud-master** | `.agents/skills/mud-master` | **整合Skill** - 一站式开发助手（规划+编码+审查） | ⭐⭐⭐ 推荐 |
| mud-architect | `.agents/skills/mud_architect` | 架构规划与阶段管理（单独使用） | ⭐⭐ 可选 |
| mud-coder | `.agents/skills/mud_coder` | 代码模板与实现指导（单独使用） | ⭐⭐ 可选 |
| mud-reviewer | `.agents/skills/mud_reviewer` | 代码审查与验收检查（单独使用） | ⭐⭐ 可选 |

## 推荐使用方式

### 方式一：整合Skill（推荐）

使用 `mud-master` 一个 Skill 完成完整开发工作流：

```
# 一句话启动完整开发循环
@mud-master 启动阶段一，实现Typeclass动态类系统

→ 自动规划阶段
→ 自动生成代码  
→ 自动审查代码
→ 输出报告和建议
```

**优势**：
- 一次对话完成规划→编码→审查完整流程
- 自动循环迭代（修复→重审）
- 无需手动切换Skill

### 方式二：单独Skill（灵活）

根据需要使用单个Skill：

```
@mud-architect 规划阶段二
@mud-coder 生成Character类代码
@mud-reviewer 审查这段代码
```

**优势**：
- 更细粒度的控制
- 可只使用部分功能

## 使用示例

### mud-master 完整工作流

```
用户：@mud-master 启动阶段一，实现项目骨架模块

mud-master:
  ═══════════════════════════════════════════════════
  [步骤1/3] 规划阶段
  ═══════════════════════════════════════════════════
  阶段：阶段一 - 引擎核心搭建
  模块：项目骨架
  
  ═══════════════════════════════════════════════════
  [步骤2/3] 生成代码
  ═══════════════════════════════════════════════════
  生成：src/utils/config.py
  生成：src/utils/logging.py
  生成：pyproject.toml
  
  ═══════════════════════════════════════════════════
  [步骤3/3] 代码审查
  ═══════════════════════════════════════════════════
  审查结果：通过 ✓
  
  模块已完成，是否继续下一模块？(是/否)
```

### mud-master 分步使用

```
用户：@mud-master 阶段二有哪些模块？
→ 列出阶段二模块清单

用户：@mud-master 生成装备系统的代码
→ 生成Equipment类和相关代码

用户：@mud-master 审查这段代码 [粘贴代码]
→ 输出审查报告
```

## Skill 详细内容

### mud-master（整合Skill）

包含原三个Skill的所有功能：

**1. 架构规划**
- 六阶段开发路线图（阶段一至六）
- 模块清单与依赖关系
- 验收标准检查

**2. 代码编写**
- 所有系统代码模板：
  - 核心系统：Typeclass、Command、EventScheduler、GameEngine、存档
  - 游戏内容：Character、装备、武学、地图、战斗、任务、NPC
  - GUI系统：PySide6、面板、主题
  - 项目基础：目录结构、配置、日志

**3. 代码审查**
- 各系统详细检查清单
- 性能指标检查（响应时间<100ms、内存<500MB等）
- 测试覆盖要求（>80%）
- 问题分级与修复建议

### 原有Skill（单独使用）

如需单独使用，请参考各Skill的SKILL.md：
- `mud_architect/SKILL.md`
- `mud_coder/SKILL.md`
- `mud_reviewer/SKILL.md`

## 开发工作流对比

### 整合工作流（mud-master）

```
用户一句话启动
    ↓
mud-master 自动完成：
    规划 → 编码 → 审查 → 修复 → 通过 → 下一模块
    ↑___________________________________________|
```

### 分步工作流（原三个Skill）

```
mud-architect 规划
    ↓
mud-coder 编码
    ↓
mud-reviewer 审查
    ↓ 不通过
  回到 mud-coder
    ↓ 通过
  回到 mud-architect
```

## 选择建议

| 场景 | 推荐Skill | 原因 |
|:---|:---|:---|
| 新用户/快速开发 | **mud-master** | 一站式，无需学习多个Skill |
| 只需要查看规划 | mud-architect | 轻量，专注规划 |
| 只需要代码模板 | mud-coder | 快速获取代码 |
| 只需要审查 | mud-reviewer | 专注质量控制 |
| 高度定制化流程 | 三个单独Skill | 灵活组合，精细控制 |

# 金庸武侠MUD - Project Skills

## Project-Local Skill

本项目只保留一个本地 Skill：

| Skill | 路径 | 用途 |
|:---|:---|:---|
| **mud-master** | `.agents/skills/mud-master` | 项目唯一入口；负责阶段规划、模块实现、代码审查、验收检查和修复迭代 |

## 使用原则

- 需要规划、编码、补测试、审查、验收或修复时，统一使用 `mud-master`。
- 不再维护 `mud_architect`、`mud_coder`、`mud_reviewer`，也不要在提示词或文档中继续引用它们。
- 优先让 `mud-master` 读取最小必要的 `references/` 文档，再结合仓库现状执行任务。

## 常见请求示例

```text
启动阶段一并列出推荐的实现顺序
实现 Character 装备系统并补单元测试
审查这次改动，按严重程度列出问题
对照阶段验收标准检查当前完成度
```

## 维护约定

- `mud-master` 的 `references/` 视为当前唯一维护版本。
- 如果 reference 与仓库代码不一致，应优先修正 Skill 文档或明确说明差异。

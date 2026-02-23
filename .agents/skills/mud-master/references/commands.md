# Command系统实现指南

## 核心概念

Command系统处理玩家输入的命令，包括：

1. **Command基类** - 定义命令结构和执行流程
2. **CmdSet集合** - 管理可用的命令集合
3. **命令解析** - 输入到命令的映射
4. **权限控制** - 基于锁的权限检查

## 实现要点

### 1. 命令解析流程

```
用户输入 → 预处理 → 分割命令和参数 → Trie匹配 → 权限检查 → 执行
```

### 2. Trie树前缀匹配

```python
class CommandTrie:
    """命令前缀树，支持模糊匹配。"""
    
    def __init__(self) -> None:
        self.root: dict[str, Any] = {}
    
    def add(self, key: str, cmd: Type[Command]) -> None:
        """添加命令到Trie树。"""
        node = self.root
        for char in key:
            if char not in node:
                node[char] = {}
            node = node[char]
        node["_cmd"] = cmd
    
    def match(self, prefix: str) -> Optional[Type[Command]]:
        """根据前缀匹配命令。"""
        node = self.root
        for char in prefix:
            if char not in node:
                return None
            node = node[char]
        return node.get("_cmd")
```

### 3. 权限锁系统

锁字符串格式：`"type:condition"`

- `perm:admin` - 需要admin权限
- `hold:key` - 需要持有某key
- `loc:room_id` - 需要在指定位置

### 4. 具体命令实现示例

```python
class CmdLook(Command):
    """查看命令。
    
    用法: look [目标]
    """
    
    key = "look"
    aliases = ["l", "看"]
    locks = ""
    help_text = "查看周围环境或指定目标"
    
    def execute(self) -> None:
        """执行查看。"""
        if not self.args:
            # 查看当前位置
            location = self.caller.location
            self.caller.msg(location.get_desc())
        else:
            # 查看指定目标
            target = self.caller.search(self.args)
            if target:
                self.caller.msg(target.get_desc())
```

## 注意事项

1. 命令解析优先匹配完整匹配，然后前缀匹配
2. 多个命令匹配相同前缀时，列出所有选项
3. 权限检查失败应给出明确提示
4. 命令执行异常需要捕获并记录

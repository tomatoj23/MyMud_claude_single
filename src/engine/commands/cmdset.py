"""命令集合管理.

提供CmdSet类和CommandTrie树实现。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from src.engine.commands.command import Command
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CommandTrie:
    """命令前缀树.

    支持快速前缀匹配命令。
    """

    def __init__(self) -> None:
        """初始化前缀树."""
        self.root: dict[str, Any] = {}

    def add(self, key: str, cmd_class: type[Command]) -> None:
        """添加命令到前缀树.

        Args:
            key: 命令键
            cmd_class: 命令类
        """
        node = self.root
        for char in key.lower():
            if char not in node:
                node[char] = {}
            node = node[char]
        node["_cmd"] = cmd_class

    def match(self, prefix: str) -> type[Command] | None:
        """根据前缀匹配命令.

        Args:
            prefix: 命令前缀

        Returns:
            匹配的命令类或None
        """
        node = self.root

        # 先走到前缀节点
        for char in prefix.lower():
            if char not in node:
                return None
            node = node[char]

        # 如果完全匹配，直接返回
        if "_cmd" in node:
            return node["_cmd"]

        # 查找所有子命令（去重）
        matches: list[type[Command]] = []
        seen: set[type[Command]] = set()
        self._collect_commands(node, matches)

        # 去重
        unique_matches = []
        for cmd in matches:
            if cmd not in seen:
                seen.add(cmd)
                unique_matches.append(cmd)

        # 如果只有一个唯一子命令，返回它
        if len(unique_matches) == 1:
            return unique_matches[0]

        return None

    def get_matches(self, prefix: str) -> list[type[Command]]:
        """获取所有前缀匹配的命令.

        Args:
            prefix: 命令前缀

        Returns:
            匹配的命令类列表
        """
        node = self.root
        for char in prefix.lower():
            if char not in node:
                return []
            node = node[char]

        # 收集所有匹配的命令
        matches: list[type[Command]] = []
        self._collect_commands(node, matches)
        return matches

    def _collect_commands(self, node: dict, matches: list) -> None:
        """递归收集命令.

        Args:
            node: 当前节点
            matches: 结果列表
        """
        if "_cmd" in node:
            matches.append(node["_cmd"])

        for key, child in node.items():
            if key != "_cmd":
                self._collect_commands(child, matches)


class CmdSet:
    """命令集合.

    管理一组可用命令，支持优先级合并。

    Attributes:
        key: 集合标识
        priority: 优先级（越高越优先）
        mergetype: 合并类型
    """

    # 合并类型
    MERGE_REPLACE = "replace"  # 完全替换
    MERGE_ADD = "add"  # 添加新命令
    MERGE_REMOVE = "remove"  # 移除命令

    def __init__(
        self,
        key: str = "default",
        priority: int = 0,
        mergetype: str = MERGE_ADD,
    ) -> None:
        """初始化命令集合.

        Args:
            key: 集合标识
            priority: 优先级
            mergetype: 合并类型
        """
        self.key = key
        self.priority = priority
        self.mergetype = mergetype

        # 命令字典: key -> Command类
        self.commands: dict[str, type[Command]] = {}
        self.trie = CommandTrie()

    def add(self, cmd_class: type[Command]) -> CmdSet:
        """添加命令.

        Args:
            cmd_class: 命令类

        Returns:
            self（链式调用）
        """
        self.commands[cmd_class.key] = cmd_class
        self.trie.add(cmd_class.key, cmd_class)

        # 添加别名
        for alias in cmd_class.aliases:
            self.trie.add(alias, cmd_class)

        return self

    def remove(self, cmd_key: str) -> CmdSet:
        """移除命令.

        Args:
            cmd_key: 命令键

        Returns:
            self（链式调用）
        """
        if cmd_key in self.commands:
            del self.commands[cmd_key]
            # 重建前缀树
            self._rebuild_trie()
        return self

    def _rebuild_trie(self) -> None:
        """重建前缀树."""
        self.trie = CommandTrie()
        for cmd_class in self.commands.values():
            self.trie.add(cmd_class.key, cmd_class)
            for alias in cmd_class.aliases:
                self.trie.add(alias, cmd_class)

    def get(self, cmd_key: str) -> type[Command] | None:
        """获取命令类.

        Args:
            cmd_key: 命令键

        Returns:
            命令类或None
        """
        return self.commands.get(cmd_key)

    def match(self, cmd_string: str) -> type[Command] | None:
        """匹配命令.

        先尝试完整匹配，然后前缀匹配。

        Args:
            cmd_string: 命令字符串

        Returns:
            匹配的命令类或None
        """
        # 完整匹配
        cmd_lower = cmd_string.lower()
        if cmd_lower in self.commands:
            return self.commands[cmd_lower]

        # 前缀匹配
        return self.trie.match(cmd_lower)

    def get_matches(self, prefix: str) -> list[type[Command]]:
        """获取所有匹配的命令.

        Args:
            prefix: 前缀

        Returns:
            命令类列表
        """
        return self.trie.get_matches(prefix)

    def merge(self, other: CmdSet) -> CmdSet:
        """合并另一个命令集合.

        Args:
            other: 另一个命令集合

        Returns:
            合并后的新集合
        """
        # 根据优先级决定合并方式
        if other.priority > self.priority:
            # 对方优先级高，以对方为基础
            base = CmdSet(
                key=f"{self.key}+{other.key}",
                priority=other.priority,
            )

            if other.mergetype == self.MERGE_REPLACE:
                # 完全替换
                base.commands = other.commands.copy()
            elif other.mergetype == self.MERGE_REMOVE:
                # 移除指定命令
                base.commands = {
                    k: v for k, v in self.commands.items()
                    if k not in other.commands
                }
            else:  # MERGE_ADD
                # 合并，对方命令覆盖
                base.commands = self.commands.copy()
                base.commands.update(other.commands)
        else:
            # 己方优先级高
            base = CmdSet(
                key=f"{self.key}+{other.key}",
                priority=self.priority,
            )

            if self.mergetype == self.MERGE_REPLACE:
                base.commands = self.commands.copy()
            elif self.mergetype == self.MERGE_REMOVE:
                base.commands = {
                    k: v for k, v in other.commands.items()
                    if k not in self.commands
                }
            else:  # MERGE_ADD
                base.commands = self.commands.copy()
                base.commands.update(other.commands)

        base._rebuild_trie()
        return base

    def __add__(self, other: CmdSet) -> CmdSet:
        """+ 操作符合并."""
        return self.merge(other)

    def __iter__(self) -> Iterator[type[Command]]:
        """迭代命令."""
        return iter(self.commands.values())

    def __len__(self) -> int:
        """命令数量."""
        return len(self.commands)

    def __contains__(self, cmd_key: str) -> bool:
        """检查是否包含命令."""
        return cmd_key in self.commands

    def __bool__(self) -> bool:
        """是否有命令."""
        return bool(self.commands)

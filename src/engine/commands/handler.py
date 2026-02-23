"""命令处理器.

提供命令解析和执行的主处理器。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.engine.commands.cmdset import CmdSet
from src.engine.commands.command import CommandResult
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine
    from src.engine.core.typeclass import TypeclassBase

logger = get_logger(__name__)


class CommandHandler:
    """命令处理器.

    处理玩家输入的命令解析和执行。

    Attributes:
        engine: 游戏引擎
        default_cmdset: 默认命令集合
    """

    def __init__(self, engine: GameEngine) -> None:
        """初始化命令处理器.

        Args:
            engine: 游戏引擎
        """
        self.engine = engine
        self.default_cmdset = CmdSet("default", priority=0)
        self._initialized = False

    async def initialize(self) -> None:
        """初始化命令处理器."""
        if self._initialized:
            return

        logger.info("正在初始化命令处理器...")

        # 注册默认命令
        self._register_default_commands()

        self._initialized = True
        logger.info("命令处理器初始化完成")

    def _register_default_commands(self) -> None:
        """注册默认命令."""
        # 导入并注册基础命令
        from src.engine.commands.default import (
            CmdCreate,
            CmdDestroy,
            CmdInventory,
            CmdLook,
            CmdMove,
        )

        self.default_cmdset.add(CmdLook)
        self.default_cmdset.add(CmdMove)
        self.default_cmdset.add(CmdInventory)
        self.default_cmdset.add(CmdCreate)
        self.default_cmdset.add(CmdDestroy)

        logger.debug(f"注册了 {len(self.default_cmdset)} 个默认命令")

    def get_cmdset(self, _caller: TypeclassBase) -> CmdSet:
        """获取调用者的可用命令集合.

        Args:
            caller: 调用者

        Returns:
            命令集合
        """
        # 基础命令集合
        cmdset = self.default_cmdset

        # TODO: 从调用者位置获取可用命令
        # TODO: 从调用者自身获取可用命令

        return cmdset

    async def handle(
        self,
        caller: TypeclassBase,
        raw_input: str,
        session: Any = None,
    ) -> CommandResult:
        """处理玩家输入.

        Args:
            caller: 调用者
            raw_input: 原始输入
            session: 会话对象

        Returns:
            命令执行结果
        """
        if not raw_input.strip():
            return CommandResult(True)  # 空输入视为成功

        # 预处理输入
        cmd_string, args = self._parse_input(raw_input)
        if not cmd_string:
            return CommandResult(True)

        # 获取可用命令
        cmdset = self.get_cmdset(caller)

        # 查找命令
        cmd_class = cmdset.match(cmd_string)
        if cmd_class is None:
            return CommandResult(
                False,
                f"未知命令: '{cmd_string}'。输入 'help' 查看可用命令。"
            )

        # 检查是否有多个匹配
        matches = cmdset.get_matches(cmd_string)
        if len(matches) > 1:
            # 如果有完全匹配，使用完全匹配
            exact_match = cmdset.get(cmd_string)
            if exact_match:
                cmd_class = exact_match
            else:
                # 列出所有匹配
                names = [cmd.key for cmd in matches[:5]]
                return CommandResult(
                    False,
                    f"有多个命令匹配 '{cmd_string}': {', '.join(names)}"
                )

        # 创建命令实例
        cmd = cmd_class()
        cmd.caller = caller
        cmd.args = args
        cmd.cmdstring = cmd_string
        cmd.session = session

        # 执行命令
        return await cmd.run()

    def _parse_input(self, raw_input: str) -> tuple[str, str]:
        """解析输入字符串.

        分割命令和参数。

        Args:
            raw_input: 原始输入

        Returns:
            (命令, 参数) 元组
        """
        # 去除首尾空白
        input_str = raw_input.strip()
        if not input_str:
            return "", ""

        # 分割命令和参数
        # 支持引号内的参数
        parts = self._split_args(input_str)
        if not parts:
            return "", ""

        cmd_string = parts[0].lower()
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        return cmd_string, args

    def _split_args(self, input_str: str) -> list[str]:
        """分割参数.

        支持引号内的空格。

        Args:
            input_str: 输入字符串

        Returns:
            参数列表
        """
        # 简单实现：按空白分割
        # 阶段三实现更复杂的参数解析
        return input_str.split()

    async def execute_command(
        self,
        caller: TypeclassBase,
        cmd_key: str,
        args: str = "",
        session: Any = None,
    ) -> CommandResult:
        """直接执行指定命令.

        Args:
            caller: 调用者
            cmd_key: 命令键
            args: 命令参数
            session: 会话对象

        Returns:
            执行结果
        """
        cmdset = self.get_cmdset(caller)
        cmd_class = cmdset.get(cmd_key)

        if cmd_class is None:
            return CommandResult(False, f"未知命令: {cmd_key}")

        cmd = cmd_class()
        cmd.caller = caller
        cmd.args = args
        cmd.cmdstring = cmd_key
        cmd.session = session

        return await cmd.run()

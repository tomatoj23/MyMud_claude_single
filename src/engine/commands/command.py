"""命令基类定义.

提供Command基类和CommandResult结果类。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from src.utils.logging import get_logger
from src.engine.core.messages import MessageBus, get_message_bus, MessageType

if TYPE_CHECKING:
    from src.engine.core.typeclass import TypeclassBase

logger = get_logger(__name__)


@dataclass
class CommandResult:
    """命令执行结果.

    Attributes:
        success: 是否成功
        message: 结果消息
        data: 额外数据
    """

    success: bool
    message: str = ""
    data: dict[str, Any] | None = None


class Command:
    """命令基类.

    所有游戏命令的基类，定义命令结构和执行流程。

    Attributes:
        key: 命令主键
        aliases: 命令别名列表
        locks: 权限锁字符串
        help_category: 帮助分类
        help_text: 帮助文本
        priority: 优先级（越高越优先）
    """

    # 类属性（子类可重写）
    key: ClassVar[str] = ""
    aliases: ClassVar[list[str]] = []
    locks: ClassVar[str] = ""
    help_category: ClassVar[str] = "general"
    help_text: ClassVar[str] = ""
    priority: ClassVar[int] = 0

    def __init__(self) -> None:
        """初始化命令实例."""
        # 运行时属性
        self.caller: TypeclassBase | None = None
        self.args: str = ""
        self.cmdstring: str = ""
        self.cmdset_source: str = ""
        self.session: Any = None

    def __str__(self) -> str:  # noqa: D105
        return f"<{self.__class__.__name__}: {self.key}>"

    def __repr__(self) -> str:  # noqa: D105
        return self.__str__()

    def has_perm(self, _caller: TypeclassBase) -> bool:
        """检查调用者是否有权限执行此命令.

        Args:
            caller: 调用者

        Returns:
            是否有权限
        """
        # 简化实现：空锁表示无限制
        if not self.locks:
            return True

        # TODO: 实现完整的锁检查逻辑
        # 阶段六实现完整权限系统
        return True

    def parse(self) -> bool:
        """解析命令参数.

        子类可重写此方法进行参数解析。

        Returns:
            解析是否成功
        """
        return True

    async def execute(self) -> CommandResult:
        """执行命令.

        子类必须实现此方法。

        Returns:
            执行结果

        Raises:
            NotImplementedError: 未实现
        """
        raise NotImplementedError(f"命令 {self.key} 未实现 execute 方法")

    async def run(self) -> CommandResult:
        """完整执行流程.

        1. 权限检查
        2. 参数解析
        3. 执行命令

        Returns:
            执行结果
        """
        if self.caller is None:
            return CommandResult(False, "调用者未设置")

        # 权限检查
        if not self.has_perm(self.caller):
            return CommandResult(False, "你没有权限执行此命令。")

        # 参数解析
        if not self.parse():
            return CommandResult(False, "参数解析失败。")

        try:
            # 执行命令
            return await self.execute()
        except Exception as e:
            logger.exception(f"命令执行错误: {self.key}")
            return CommandResult(False, f"命令执行出错: {e}")

    def msg(
        self,
        text: str,
        msg_type: MessageType | str = MessageType.SYSTEM,
        **kwargs: Any
    ) -> None:
        """向调用者发送消息.
        
        支持消息总线，如果GUI连接了消息总线，消息会显示在GUI中。

        Args:
            text: 消息文本
            msg_type: 消息类型
            **kwargs: 额外参数
        """
        # 优先使用消息总线
        if hasattr(self.caller, 'message_bus') and self.caller.message_bus:
            self.caller.message_bus.emit_text(msg_type, text, **kwargs)
        elif hasattr(self.caller, 'msg'):
            # 回退到直接调用
            self.caller.msg(text, **kwargs)
        else:
            # 使用全局消息总线
            bus = get_message_bus()
            bus.emit_text(msg_type, text, **kwargs)

    def search(
        self,
        search_string: str,
        candidates: list[Any] | None = None,
        nofound_string: str = "",
        multimatch_string: str = "",
    ) -> Any | None:
        """搜索目标对象.

        Args:
            search_string: 搜索字符串
            candidates: 候选对象列表（默认搜索调用者位置的内容）
            nofound_string: 未找到时的提示
            multimatch_string: 多个匹配时的提示

        Returns:
            找到的对象或None
        """
        if not self.caller:
            return None

        if candidates is None:
            # 默认搜索位置内容
            if self.caller.location:
                candidates = self.caller.location.contents + [self.caller.location]
            else:
                candidates = []

        # 简单搜索：按key匹配
        matches = [
            obj for obj in candidates
            if hasattr(obj, "key") and search_string.lower() in obj.key.lower()
        ]

        if not matches:
            if nofound_string:
                self.msg(nofound_string)
            return None

        if len(matches) > 1:
            if multimatch_string:
                names = ", ".join(obj.key for obj in matches[:5])
                self.msg(f"{multimatch_string} [{names}]")
            return matches[0]  # 返回第一个匹配

        return matches[0]

    def get_help(self) -> str:
        """获取命令帮助文本.

        Returns:
            帮助文本
        """
        lines = [
            f"命令: {self.key}",
            f"别名: {', '.join(self.aliases) if self.aliases else '无'}",
            f"分类: {self.help_category}",
            "",
            self.help_text or "暂无帮助信息。",
        ]
        return "\n".join(lines)

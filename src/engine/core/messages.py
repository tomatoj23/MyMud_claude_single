"""消息总线系统 - 引擎与GUI之间的消息传递接口.

提供统一的输出接口，支持文本消息、状态更新、事件通知等。
可以与PySide6的信号系统集成，也可以独立使用。
"""
from __future__ import annotations

import logging
from typing import Any, Callable
from enum import Enum, auto
import time
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举."""
    
    SYSTEM = "system"           # 系统消息
    ERROR = "error"             # 错误消息
    WARNING = "warning"         # 警告消息
    INFO = "info"               # 信息消息
    DEBUG = "debug"             # 调试消息
    
    COMBAT = "combat"           # 战斗消息
    DIALOGUE = "dialogue"       # 对话消息
    NOTIFICATION = "notify"     # 通知消息
    
    STATUS = "status"           # 状态更新
    PROMPT = "prompt"           # 输入提示


class Message:
    """消息对象.
    
    Attributes:
        msg_type: 消息类型
        content: 消息内容
        data: 附加数据
        timestamp: 时间戳
    """
    
    def __init__(
        self,
        msg_type: MessageType | str,
        content: str,
        data: dict[str, Any] | None = None
    ):
        """初始化消息.
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            data: 附加数据
        """
        self.msg_type = msg_type if isinstance(msg_type, MessageType) else MessageType(msg_type)
        self.content = content
        self.data = data or {}
        # 使用标准时间戳，不依赖事件循环（避免RuntimeError）
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        return f"[{self.msg_type.value}] {self.content}"
    
    def __repr__(self) -> str:
        return f"Message({self.msg_type.value}, {self.content[:50]!r})"


class MessageHandler:
    """消息处理器基类.
    
    所有需要接收消息的类都应继承此类。
    """
    
    def __init__(self):
        """初始化消息处理器."""
        self._message_bus: MessageBus | None = None
    
    @property
    def message_bus(self) -> MessageBus | None:
        """获取消息总线."""
        return self._message_bus
    
    @message_bus.setter
    def message_bus(self, bus: MessageBus | None) -> None:
        """设置消息总线."""
        self._message_bus = bus
    
    def msg(self, text: str, msg_type: MessageType | str = MessageType.SYSTEM, **kwargs) -> None:
        """发送消息.
        
        Args:
            text: 消息内容
            msg_type: 消息类型
            **kwargs: 附加数据
        """
        if self._message_bus:
            self._message_bus.emit(Message(msg_type, text, kwargs))
        else:
            # 如果没有消息总线，打印到控制台
            logger.info(f"[{msg_type}] {text}")
    
    def msg_system(self, text: str, **kwargs) -> None:
        """发送系统消息."""
        self.msg(text, MessageType.SYSTEM, **kwargs)
    
    def msg_error(self, text: str, **kwargs) -> None:
        """发送错误消息."""
        self.msg(text, MessageType.ERROR, **kwargs)
    
    def msg_info(self, text: str, **kwargs) -> None:
        """发送信息消息."""
        self.msg(text, MessageType.INFO, **kwargs)
    
    def msg_combat(self, text: str, **kwargs) -> None:
        """发送战斗消息."""
        self.msg(text, MessageType.COMBAT, **kwargs)
    
    def emit_status(self, status_type: str, data: dict[str, Any]) -> None:
        """发送状态更新.
        
        Args:
            status_type: 状态类型
            data: 状态数据
        """
        if self._message_bus:
            self._message_bus.emit_status(status_type, data)


class MessageBus:
    """消息总线.
    
    负责消息的接收、分发和管理。
    可以与PySide6信号系统集成。
    """
    
    def __init__(self, max_history: int = 1000):
        """初始化消息总线.
        
        Args:
            max_history: 最大历史消息数
        """
        self._handlers: list[Callable[[Message], None]] = []
        self._status_handlers: dict[str, list[Callable[[dict], None]]] = {}
        self._history: deque[Message] = deque(maxlen=max_history)
        self._enabled = True
    
    def emit(self, message: Message) -> None:
        """发送消息.
        
        Args:
            message: 消息对象
        """
        if not self._enabled:
            return
        
        # 保存到历史
        self._history.append(message)
        
        # 分发给所有处理器
        for handler in self._handlers:
            try:
                handler(message)
            except Exception as e:
                logger.exception(f"Message handler error: {e}")
    
    def emit_text(self, msg_type: MessageType | str, content: str, **data) -> None:
        """发送文本消息.
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            **data: 附加数据
        """
        self.emit(Message(msg_type, content, data))
    
    def emit_status(self, status_type: str, data: dict[str, Any]) -> None:
        """发送状态更新.
        
        Args:
            status_type: 状态类型
            data: 状态数据
        """
        if not self._enabled:
            return
        
        handlers = self._status_handlers.get(status_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.exception(f"Status handler error: {e}")
    
    def subscribe(self, handler: Callable[[Message], None]) -> None:
        """订阅消息.
        
        Args:
            handler: 消息处理器
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def unsubscribe(self, handler: Callable[[Message], None]) -> None:
        """取消订阅消息.
        
        Args:
            handler: 消息处理器
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def subscribe_status(
        self,
        status_type: str,
        handler: Callable[[dict], None]
    ) -> None:
        """订阅状态更新.
        
        Args:
            status_type: 状态类型
            handler: 状态处理器
        """
        if status_type not in self._status_handlers:
            self._status_handlers[status_type] = []
        if handler not in self._status_handlers[status_type]:
            self._status_handlers[status_type].append(handler)
    
    def unsubscribe_status(
        self,
        status_type: str,
        handler: Callable[[dict], None]
    ) -> None:
        """取消订阅状态更新.
        
        Args:
            status_type: 状态类型
            handler: 状态处理器
        """
        if status_type in self._status_handlers:
            if handler in self._status_handlers[status_type]:
                self._status_handlers[status_type].remove(handler)
    
    def get_history(
        self,
        msg_type: MessageType | str | None = None,
        limit: int = 100
    ) -> list[Message]:
        """获取历史消息.
        
        Args:
            msg_type: 消息类型过滤
            limit: 返回数量限制
            
        Returns:
            历史消息列表
        """
        messages = list(self._history)
        
        if msg_type is not None:
            target_type = msg_type if isinstance(msg_type, MessageType) else MessageType(msg_type)
            messages = [m for m in messages if m.msg_type == target_type]
        
        return messages[-limit:]
    
    def clear_history(self) -> None:
        """清空历史消息."""
        self._history.clear()
    
    def enable(self) -> None:
        """启用消息总线."""
        self._enabled = True
    
    def disable(self) -> None:
        """禁用消息总线."""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """是否启用."""
        return self._enabled


# 全局消息总线实例
_global_message_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """获取全局消息总线.
    
    Returns:
        全局消息总线实例
    """
    global _global_message_bus
    if _global_message_bus is None:
        _global_message_bus = MessageBus()
    return _global_message_bus


def set_message_bus(bus: MessageBus) -> None:
    """设置全局消息总线.
    
    Args:
        bus: 消息总线实例
    """
    global _global_message_bus
    _global_message_bus = bus

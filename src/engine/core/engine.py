"""游戏引擎核心.

整合所有子系统的主引擎类。
"""

from __future__ import annotations

import asyncio
import inspect
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.engine.database.connection import DatabaseManager
from src.engine.events.scheduler import EventScheduler
from src.engine.core.messages import MessageBus, get_message_bus
from src.utils.config import Config, get_config
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.engine.commands.handler import CommandHandler
    from src.engine.objects.manager import ObjectManager

logger = get_logger(__name__)


class GameEngine:
    """游戏引擎核心 - 协调所有子系统.

    主要职责：
    1. 初始化和协调各子系统
    2. 处理游戏主循环
    3. 管理引擎生命周期（启动/停止）
    4. 处理玩家输入

    Attributes:
        config: 配置管理器
        db: 数据库管理器
        objects: 对象管理器
        commands: 命令处理器
        events: 事件调度器
        running: 引擎运行状态
    """

    def __init__(
        self,
        config: Config | None = None,
        message_bus: MessageBus | None = None,
        scheduler: EventScheduler | None = None
    ) -> None:
        """初始化引擎（不启动子系统）.

        Args:
            config: 配置对象，None则使用全局配置
            message_bus: 消息总线，None则使用全局实例
            scheduler: 事件调度器，None则使用默认EventScheduler
        """
        self.config = config or get_config()

        # 消息总线
        self._message_bus = message_bus or get_message_bus()

        # 子系统（延迟初始化）
        self._db: DatabaseManager | None = None
        self._objects: ObjectManager | None = None
        self._commands: CommandHandler | None = None
        self._events: EventScheduler | None = None
        self._injected_scheduler = scheduler

        self._running = False
        self._main_task: asyncio.Task[Any] | None = None
        self._auto_save_task: asyncio.Task[Any] | None = None

        logger.info("游戏引擎实例已创建")

    @property
    def db(self) -> DatabaseManager:
        """获取数据库管理器."""
        if self._db is None:
            raise RuntimeError("引擎未初始化")
        return self._db

    @property
    def objects(self) -> ObjectManager:
        """获取对象管理器."""
        if self._objects is None:
            raise RuntimeError("引擎未初始化")
        return self._objects

    @property
    def commands(self) -> CommandHandler:
        """获取命令处理器."""
        if self._commands is None:
            raise RuntimeError("引擎未初始化")
        return self._commands

    @property
    def events(self) -> EventScheduler | None:
        """获取事件调度器."""
        if self._events is None:
            raise RuntimeError("引擎未初始化")
        return self._events

    @property
    def message_bus(self) -> MessageBus:
        """获取消息总线."""
        return self._message_bus
    
    @property
    def running(self) -> bool:
        """引擎是否正在运行."""
        return self._running

    async def initialize(self) -> None:
        """初始化所有子系统.

        初始化顺序：
        1. 数据库连接
        2. 对象管理器
        3. 命令处理器
        4. 事件调度器
        """
        logger.info("正在初始化游戏引擎...")

        # 1. 初始化数据库
        db_path = Path(self.config.database.url.replace("sqlite+aiosqlite:///", ""))
        self._db = DatabaseManager(db_path)
        await self._db.initialize()
        logger.info("数据库初始化完成")

        # 2. 初始化对象管理器
        from src.engine.objects.manager import ObjectManager
        self._objects = ObjectManager(self._db)
        await self._objects.initialize()
        logger.info("对象管理器初始化完成")

        # 3. 初始化命令处理器
        from src.engine.commands.handler import CommandHandler
        self._commands = CommandHandler(self)
        await self._commands.initialize()
        logger.info("命令处理器初始化完成")

        # 4. 初始化事件调度器
        if self._injected_scheduler:
            self._events = self._injected_scheduler
            logger.info("使用注入的事件调度器")
        else:
            self._events = EventScheduler(self.config.game.tick_rate)
            logger.info("事件调度器初始化完成")

        logger.info("游戏引擎初始化完成")

    async def start(self) -> None:
        """启动引擎主循环."""
        if self._running:
            raise RuntimeError("引擎已在运行")

        if self._db is None:
            raise RuntimeError("引擎未初始化")

        logger.info("启动游戏引擎...")
        self._running = True

        # 启动事件调度器
        if self._events:
            if inspect.iscoroutinefunction(self._events.start):
                await self._events.start()
            else:
                self._events.start()

        # 启动自动保存任务
        self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        logger.info("游戏引擎已启动")

    async def stop(self) -> None:
        """停止引擎（优雅关闭）.

        关闭顺序：
        1. 停止接受新输入
        2. 保存所有dirty对象
        3. 停止事件调度器
        4. 关闭数据库连接
        """
        if not self._running:
            return

        logger.info("正在停止游戏引擎...")
        self._running = False

        # 停止自动保存任务
        if self._auto_save_task and not self._auto_save_task.done():
            self._auto_save_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._auto_save_task

        # 保存所有dirty对象
        if self._objects:
            await self._objects.save_all()
            logger.info("所有对象已保存")

        # 停止事件调度器
        if self._events:
            if inspect.iscoroutinefunction(self._events.stop):
                await self._events.stop()
            else:
                self._events.stop()
            logger.info("事件调度器已停止")

        # 关闭数据库连接
        if self._db:
            await self._db.close()
            logger.info("数据库连接已关闭")

        logger.info("游戏引擎已停止")

    async def _auto_save_loop(self) -> None:
        """自动保存循环."""
        interval = self.config.game.auto_save_interval  # 默认5分钟

        while self._running:
            try:
                await asyncio.sleep(interval)
                if self._objects:
                    count = await self._objects.save_all()
                    if count > 0:
                        logger.info(f"自动保存: {count} 个对象")
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("自动保存出错")

    async def process_input(
        self,
        caller: Any,
        text: str,
        session: Any = None,
    ) -> Any:
        """处理玩家输入.

        Args:
            caller: 调用者
            text: 输入文本
            session: 会话对象

        Returns:
            命令执行结果
        """
        if not self._running:
            return None

        if not self._commands:
            raise RuntimeError("引擎未初始化")

        try:
            result = await self._commands.handle(caller, text, session)
            return result
        except Exception:
            logger.exception("处理输入时出错")
            return None

    def get_stats(self) -> dict[str, Any]:
        """获取引擎统计信息.

        Returns:
            统计信息字典
        """
        stats: dict[str, Any] = {"running": self._running}

        if self._objects:
            stats["objects"] = self._objects.get_cache_stats()

        if self._events:
            stats["events"] = self._events.get_stats()

        return stats


# 全局引擎实例
_engine: GameEngine | None = None


def get_engine() -> GameEngine:
    """获取全局引擎实例.

    Returns:
        引擎实例

    Raises:
        RuntimeError: 引擎未创建
    """
    if _engine is None:
        raise RuntimeError("引擎未创建")
    return _engine


def create_engine(config: Config | None = None) -> GameEngine:
    """创建引擎实例.

    Args:
        config: 配置管理器

    Returns:
        引擎实例
    """
    global _engine
    _engine = GameEngine(config)
    return _engine

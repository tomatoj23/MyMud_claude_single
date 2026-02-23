# GameEngine 核心整合

## 概述

GameEngine是MUD游戏的核心整合类，负责协调所有子系统：数据库、对象管理、命令处理、事件调度。

## 核心架构

```
GameEngine
├── DatabaseManager (SQLite + aiosqlite)
├── ObjectManager (L1/L2缓存 + 持久化)
├── CommandHandler (命令解析 + 执行)
├── EventScheduler (延迟/周期/条件事件)
├── ConfigManager (配置管理)
└── SaveManager (存档管理)
```

## 完整实现

```python
# src/engine/core/engine.py
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..database.connection import DatabaseManager
    from ..objects.manager import ObjectManager
    from ..commands.handler import CommandHandler
    from ..events.scheduler import EventScheduler
    from ...utils.config import ConfigManager
    from ...save.manager import SaveManager


class GameEngine:
    """游戏引擎核心 - 协调所有子系统
    
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
        save: 存档管理器
        running: 引擎运行状态
    """
    
    def __init__(self, config: ConfigManager) -> None:
        """初始化引擎（不启动子系统）
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 子系统（延迟初始化）
        self._db: Optional[DatabaseManager] = None
        self._objects: Optional[ObjectManager] = None
        self._commands: Optional[CommandHandler] = None
        self._events: Optional[EventScheduler] = None
        self._save: Optional[SaveManager] = None
        
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
    
    @property
    def db(self) -> DatabaseManager:
        """获取数据库管理器"""
        if self._db is None:
            raise RuntimeError("引擎未初始化")
        return self._db
    
    @property
    def objects(self) -> ObjectManager:
        """获取对象管理器"""
        if self._objects is None:
            raise RuntimeError("引擎未初始化")
        return self._objects
    
    @property
    def commands(self) -> CommandHandler:
        """获取命令处理器"""
        if self._commands is None:
            raise RuntimeError("引擎未初始化")
        return self._commands
    
    @property
    def events(self) -> EventScheduler:
        """获取事件调度器"""
        if self._events is None:
            raise RuntimeError("引擎未初始化")
        return self._events
    
    @property
    def save(self) -> SaveManager:
        """获取存档管理器"""
        if self._save is None:
            raise RuntimeError("引擎未初始化")
        return self._save
    
    @property
    def running(self) -> bool:
        """引擎是否正在运行"""
        return self._running
    
    async def initialize(self) -> None:
        """初始化所有子系统
        
        初始化顺序：
        1. 数据库连接
        2. 对象管理器
        3. 命令处理器
        4. 事件调度器
        5. 存档管理器
        6. 加载世界数据
        """
        self.logger.info("正在初始化游戏引擎...")
        
        # 1. 初始化数据库
        from ..database.connection import DatabaseManager
        db_path = Path(self.config.get("database.path", "data/game.db"))
        self._db = DatabaseManager(db_path)
        await self._db.initialize()
        self.logger.info("数据库初始化完成")
        
        # 2. 初始化对象管理器
        from ..objects.manager import ObjectManager
        self._objects = ObjectManager(self._db)
        await self._objects.initialize()
        self.logger.info("对象管理器初始化完成")
        
        # 3. 初始化命令处理器
        from ..commands.handler import CommandHandler
        self._commands = CommandHandler(self)
        await self._commands.initialize()
        self.logger.info("命令处理器初始化完成")
        
        # 4. 初始化事件调度器
        from ..events.scheduler import EventScheduler
        time_scale = self.config.get("game.time_scale", 1.0)
        self._events = EventScheduler(time_scale)
        self.logger.info("事件调度器初始化完成")
        
        # 5. 初始化存档管理器
        from ...save.manager import SaveManager
        self._save = SaveManager(self)
        self.logger.info("存档管理器初始化完成")
        
        # 6. 加载世界数据
        await self._load_world_data()
        self.logger.info("世界数据加载完成")
        
        self.logger.info("游戏引擎初始化完成")
    
    async def _load_world_data(self) -> None:
        """加载世界数据
        
        包括：区域、房间、NPC配置等
        """
        world_path = Path(self.config.get("world.data_path", "resources/world"))
        if not world_path.exists():
            self.logger.warning(f"世界数据目录不存在: {world_path}")
            return
        
        # TODO: 从YAML文件加载世界数据
        # 阶段五实现
    
    async def start(self) -> None:
        """启动引擎主循环"""
        if self._running:
            raise RuntimeError("引擎已在运行")
        
        self.logger.info("启动游戏引擎...")
        self._running = True
        
        # 启动事件调度器
        self._main_task = asyncio.create_task(self._main_loop())
        
        self.logger.info("游戏引擎已启动")
    
    async def stop(self) -> None:
        """停止引擎（优雅关闭）
        
        关闭顺序：
        1. 停止接受新输入
        2. 保存所有dirty对象
        3. 停止事件调度器
        4. 关闭数据库连接
        """
        if not self._running:
            return
        
        self.logger.info("正在停止游戏引擎...")
        self._running = False
        
        # 1. 取消主循环任务
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        
        # 2. 保存所有dirty对象
        if self._objects:
            saved_count = await self._objects.save_all()
            self.logger.info(f"已保存 {saved_count} 个对象")
        
        # 3. 停止事件调度器
        if self._events:
            await self._events.stop()
        
        # 4. 关闭数据库连接
        if self._db:
            await self._db.close()
        
        self.logger.info("游戏引擎已停止")
    
    async def _main_loop(self) -> None:
        """引擎主循环
        
        主要负责：
        - 启动事件调度器
        - 定期保存脏数据
        - 内存清理
        """
        # 启动事件调度器
        event_task = asyncio.create_task(self._events.run())
        
        try:
            while self._running:
                # 定期自动保存（每5分钟）
                await asyncio.sleep(300)
                
                if self._objects:
                    count = await self._objects.save_all()
                    if count > 0:
                        self.logger.debug(f"自动保存 {count} 个对象")
                
                # 内存清理（如果需要）
                if self._objects:
                    self._objects.clear_cache()
                    
        except asyncio.CancelledError:
            pass
        finally:
            # 停止事件调度器
            await self._events.stop()
            if not event_task.done():
                event_task.cancel()
    
    async def process_input(
        self, 
        caller_id: int, 
        text: str
    ) -> CommandResult:
        """处理玩家输入
        
        Args:
            caller_id: 玩家对象ID
            text: 输入文本
            
        Returns:
            命令执行结果
        """
        from ..commands.base import CommandResult
        
        if not self._running:
            return CommandResult(False, "引擎未运行")
        
        # 获取玩家对象
        caller = await self._objects.get(caller_id)
        if caller is None:
            return CommandResult(False, "玩家对象不存在")
        
        # 执行命令
        result = await self._commands.execute(caller, text)
        
        # 触发自动存档（关键操作）
        if result.success and self._should_auto_save(result):
            await self._save.auto_save()
        
        return result
    
    def _should_auto_save(self, result: CommandResult) -> bool:
        """判断是否需要自动存档"""
        # 关键操作触发自动存档
        critical_commands = ["完成", "升级", "死亡", "任务"]
        return any(keyword in result.message for keyword in critical_commands)
    
    async def create_player(
        self, 
        name: str, 
        menpai: str
    ) -> Optional[int]:
        """创建新玩家
        
        Args:
            name: 玩家名称
            menpai: 门派
            
        Returns:
            新玩家对象ID，失败返回None
        """
        from ...game.typeclasses.character import Character
        
        # 创建角色对象
        player = await self._objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key=name,
            attributes={
                "menpai": menpai,
                "level": 1,
                "exp": 0,
            }
        )
        
        if player:
            # 设置初始位置（门派广场）
            start_room = await self._get_start_room(menpai)
            if start_room:
                player.location = start_room
                await self._objects.save(player)
            
            return player.id
        
        return None
    
    async def _get_start_room(
        self, 
        menpai: str
    ) -> Optional[TypeclassBase]:
        """获取门派的起始房间"""
        start_rooms = {
            "少林": "shaolin_shanmen",
            "武当": "wudang_shanmen",
            "丐帮": "gaibang_dating",
            # ... 其他门派
        }
        
        room_key = start_rooms.get(menpai)
        if room_key:
            # 通过key查找房间
            rooms = await self._objects.find(key_contains=room_key)
            return rooms[0] if rooms else None
        
        return None
```

## 启动脚本

```python
# src/main.py
import asyncio
import logging
from pathlib import Path

from src.engine.core.engine import GameEngine
from src.utils.config import ConfigManager
from src.utils.logging import setup_logging


async def main():
    """游戏主入口"""
    # 设置日志
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = ConfigManager(Path("config/game.yaml"))
    config.load()
    
    # 创建并初始化引擎
    engine = GameEngine(config)
    
    try:
        await engine.initialize()
        await engine.start()
        
        # 命令行测试模式（阶段一）
        logger.info("进入命令行测试模式")
        await cli_test_mode(engine)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        await engine.stop()


async def cli_test_mode(engine: GameEngine):
    """命令行测试模式"""
    print("=" * 50)
    print("金庸武侠MUD - 命令行测试模式")
    print("输入 'quit' 退出")
    print("=" * 50)
    
    # 创建测试玩家
    player_id = await engine.create_player("测试玩家", "少林")
    if not player_id:
        print("创建玩家失败")
        return
    
    while True:
        try:
            cmd = input("\n> ").strip()
            if cmd.lower() == "quit":
                break
            
            if not cmd:
                continue
            
            result = await engine.process_input(player_id, cmd)
            print(result.message)
            
        except EOFError:
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

## 使用示例

```python
# 创建并启动引擎
config = ConfigManager(Path("config.yaml"))
engine = GameEngine(config)

await engine.initialize()
await engine.start()

# 处理玩家输入
result = await engine.process_input(player_id, "look")
print(result.message)

# 停止引擎
await engine.stop()
```

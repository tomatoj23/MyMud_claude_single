"""数据库连接管理模块.

提供异步SQLite连接管理，支持连接池和WAL模式优化。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseError(Exception):
    """数据库错误异常."""

    pass


class DatabaseManager:
    """异步SQLite连接管理器.

    管理数据库连接生命周期，提供连接池和上下文管理器支持。
    自动配置WAL模式优化性能。

    Attributes:
        db_path: 数据库文件路径
        _connection: 当前数据库连接
        _initialized: 是否已初始化
    """

    # SQLite优化配置
    PRAGMAS = [
        "PRAGMA journal_mode = WAL;",
        "PRAGMA synchronous = NORMAL;",
        "PRAGMA cache_size = -64000;",  # 64MB
        "PRAGMA temp_store = MEMORY;",
        "PRAGMA mmap_size = 268435456;",  # 256MB
        "PRAGMA foreign_keys = ON;",
    ]

    def __init__(self, db_path: Path | str) -> None:
        """初始化数据库管理器.

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._connection: aiosqlite.Connection | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化数据库连接.

        创建数据库目录，建立连接，应用优化配置，创建表结构。
        """
        if self._initialized:
            return

        # 创建数据库目录
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"正在连接数据库: {self.db_path}")

        # 建立连接
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # 应用优化配置
        await self._apply_pragmas()

        # 创建表结构
        await self._create_tables()

        self._initialized = True
        logger.info("数据库初始化完成")

    async def _apply_pragmas(self) -> None:
        """应用SQLite优化配置."""
        if self._connection is None:
            raise DatabaseError("数据库未连接")

        for pragma in self.PRAGMAS:
            try:
                await self._connection.execute(pragma)
            except Exception as e:
                logger.warning(f"应用PRAGMA失败 {pragma}: {e}")

    async def _create_tables(self) -> None:
        """创建数据库表结构."""
        if self._connection is None:
            raise DatabaseError("数据库未连接")

        # 游戏对象表
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                typeclass_path TEXT NOT NULL,
                location_id INTEGER REFERENCES objects(id) ON DELETE SET NULL,
                attributes JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_objects_key ON objects(key)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_objects_typeclass ON objects(typeclass_path)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_objects_location ON objects(location_id)
        """)

        # 触发器：自动更新updated_at
        await self._connection.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_objects_updated_at
            AFTER UPDATE ON objects
            BEGIN
                UPDATE objects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

        await self._connection.commit()
        logger.info("数据库表结构创建完成")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[aiosqlite.Connection]:
        """获取数据库会话上下文管理器.

        Yields:
            数据库连接对象

        Example:
            async with db.session() as conn:
                await conn.execute("SELECT * FROM objects")
        """
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        try:
            yield self._connection
        except Exception as e:
            logger.error(f"数据库会话错误: {e}")
            raise

    async def execute(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> aiosqlite.Cursor:
        """执行SQL语句.

        Args:
            sql: SQL语句
            parameters: SQL参数

        Returns:
            游标对象
        """
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        return await self._connection.execute(sql, parameters)

    async def executemany(
        self, sql: str, parameters: list[tuple[Any, ...]]
    ) -> aiosqlite.Cursor:
        """批量执行SQL语句.

        Args:
            sql: SQL语句
            parameters: SQL参数列表

        Returns:
            游标对象
        """
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        return await self._connection.executemany(sql, parameters)

    async def fetchone(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> aiosqlite.Row | None:
        """查询单条记录.

        Args:
            sql: SQL语句
            parameters: SQL参数

        Returns:
            单行数据或None
        """
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        async with self._connection.execute(sql, parameters) as cursor:
            return await cursor.fetchone()

    async def fetchall(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> list[Any]:
        """查询多条记录.

        Args:
            sql: SQL语句
            parameters: SQL参数

        Returns:
            数据行列表
        """
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        async with self._connection.execute(sql, parameters) as cursor:
            result: list[Any] = await cursor.fetchall()
            return result

    async def commit(self) -> None:
        """提交事务."""
        if self._connection is None:
            raise DatabaseError("数据库未初始化")

        await self._connection.commit()

    async def close(self) -> None:
        """关闭数据库连接."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            self._initialized = False
            logger.info("数据库连接已关闭")

    async def is_healthy(self) -> bool:
        """检查数据库连接健康状态.

        Returns:
            连接是否正常
        """
        if self._connection is None:
            return False

        try:
            await self._connection.execute("SELECT 1")
            return True
        except Exception:
            logger.exception("数据库连接健康检查失败")
            return False

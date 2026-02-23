"""DatabaseManager 单元测试.

测试数据库连接、WAL模式配置、CRUD操作和健康检查。
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.engine.database.connection import DatabaseError, DatabaseManager

if TYPE_CHECKING:
    import aiosqlite


class TestDatabaseManager:
    """DatabaseManager 测试套件."""

    @pytest.fixture
    async def db(self):
        """创建临时数据库实例."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            manager = DatabaseManager(db_path)
            yield manager
            # 清理
            if manager._connection:
                await manager.close()

    @pytest.mark.asyncio
    async def test_initialize_creates_database(self, db: DatabaseManager):
        """测试初始化创建数据库文件和表结构."""
        await db.initialize()

        # 验证数据库文件已创建
        assert db.db_path.exists()
        assert db._initialized is True
        assert db._connection is not None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, db: DatabaseManager):
        """测试初始化是幂等的（多次调用不报错）."""
        await db.initialize()
        await db.initialize()  # 第二次调用应该不执行任何操作

        assert db._initialized is True

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, db: DatabaseManager):
        """测试 WAL 模式已启用."""
        await db.initialize()

        # 查询 journal_mode
        async with db.session() as conn:
            cursor = await conn.execute("PRAGMA journal_mode;")
            row = await cursor.fetchone()
            assert row[0].upper() == "WAL"

    @pytest.mark.asyncio
    async def test_foreign_keys_enabled(self, db: DatabaseManager):
        """测试外键约束已启用."""
        await db.initialize()

        async with db.session() as conn:
            cursor = await conn.execute("PRAGMA foreign_keys;")
            row = await cursor.fetchone()
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_tables_created(self, db: DatabaseManager):
        """测试表结构已创建."""
        await db.initialize()

        async with db.session() as conn:
            # 查询 objects 表是否存在
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='objects';"
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == "objects"

    @pytest.mark.asyncio
    async def test_indexes_created(self, db: DatabaseManager):
        """测试索引已创建."""
        await db.initialize()

        async with db.session() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_objects%';"
            )
            indexes = [row[0] for row in await cursor.fetchall()]
            assert "idx_objects_key" in indexes
            assert "idx_objects_typeclass" in indexes
            assert "idx_objects_location" in indexes

    @pytest.mark.asyncio
    async def test_crud_operations(self, db: DatabaseManager):
        """测试基本的 CRUD 操作."""
        import json

        await db.initialize()

        # Create
        cursor = await db.execute(
            "INSERT INTO objects (key, typeclass_path, attributes) VALUES (?, ?, ?)",
            ("test_obj", "src.test.TestObject", json.dumps({"test": True})),
        )
        await db.commit()
        obj_id = cursor.lastrowid
        assert obj_id is not None

        # Read
        row = await db.fetchone(
            "SELECT * FROM objects WHERE id = ?",
            (obj_id,),
        )
        assert row is not None
        assert row["key"] == "test_obj"
        assert row["typeclass_path"] == "src.test.TestObject"

        # Update
        await db.execute(
            "UPDATE objects SET key = ? WHERE id = ?",
            ("updated_obj", obj_id),
        )
        await db.commit()

        row = await db.fetchone(
            "SELECT key FROM objects WHERE id = ?",
            (obj_id,),
        )
        assert row["key"] == "updated_obj"

        # Delete
        await db.execute(
            "DELETE FROM objects WHERE id = ?",
            (obj_id,),
        )
        await db.commit()

        row = await db.fetchone(
            "SELECT * FROM objects WHERE id = ?",
            (obj_id,),
        )
        assert row is None

    @pytest.mark.asyncio
    async def test_fetchall_returns_list(self, db: DatabaseManager):
        """测试 fetchall 返回列表."""
        await db.initialize()

        # 插入多条记录
        for i in range(3):
            await db.execute(
                "INSERT INTO objects (key, typeclass_path) VALUES (?, ?)",
                (f"obj_{i}", "src.test.TestObject"),
            )
        await db.commit()

        rows = await db.fetchall(
            "SELECT * FROM objects WHERE typeclass_path = ?",
            ("src.test.TestObject",),
        )
        assert len(rows) == 3
        assert isinstance(rows, list)

    @pytest.mark.asyncio
    async def test_executemany(self, db: DatabaseManager):
        """测试批量执行."""
        await db.initialize()

        data = [
            ("obj_a", "src.test.TypeA"),
            ("obj_b", "src.test.TypeB"),
            ("obj_c", "src.test.TypeC"),
        ]

        await db.executemany(
            "INSERT INTO objects (key, typeclass_path) VALUES (?, ?)",
            data,
        )
        await db.commit()

        rows = await db.fetchall("SELECT * FROM objects")
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, db: DatabaseManager):
        """测试健康检查 - 健康状态."""
        await db.initialize()

        is_healthy = await db.is_healthy()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_not_initialized(self):
        """测试健康检查 - 未初始化状态."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = DatabaseManager(Path(tmpdir) / "test.db")
            is_healthy = await db.is_healthy()
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_after_close(self, db: DatabaseManager):
        """测试健康检查 - 关闭后."""
        await db.initialize()
        await db.close()

        is_healthy = await db.is_healthy()
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_session_context_manager(self, db: DatabaseManager):
        """测试会话上下文管理器."""
        await db.initialize()

        async with db.session() as conn:
            assert conn is db._connection
            cursor = await conn.execute("SELECT 1")
            row = await cursor.fetchone()
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_session_without_initialization(self, db: DatabaseManager):
        """测试未初始化时使用会话抛出异常."""
        with pytest.raises(DatabaseError, match="数据库未初始化"):
            async with db.session() as _:
                pass  # pragma: no cover

    @pytest.mark.asyncio
    async def test_execute_without_initialization(self, db: DatabaseManager):
        """测试未初始化时执行 SQL 抛出异常."""
        with pytest.raises(DatabaseError, match="数据库未初始化"):
            await db.execute("SELECT 1")

    @pytest.mark.asyncio
    async def test_trigger_updates_timestamp(self, db: DatabaseManager):
        """测试触发器自动更新 updated_at."""
        await db.initialize()

        # 插入记录
        cursor = await db.execute(
            "INSERT INTO objects (key, typeclass_path) VALUES (?, ?)",
            ("test_obj", "src.test.TestObject"),
        )
        await db.commit()
        obj_id = cursor.lastrowid

        # 获取创建时间
        row1 = await db.fetchone(
            "SELECT updated_at FROM objects WHERE id = ?",
            (obj_id,),
        )
        original_time = row1["updated_at"]

        # 等待一小段时间（SQLite 时间戳精度为秒，需要等待至少1秒）
        import asyncio

        await asyncio.sleep(1.1)

        # 更新记录
        await db.execute(
            "UPDATE objects SET key = ? WHERE id = ?",
            ("updated_obj", obj_id),
        )
        await db.commit()

        # 验证时间已更新
        row2 = await db.fetchone(
            "SELECT updated_at FROM objects WHERE id = ?",
            (obj_id,),
        )
        assert row2["updated_at"] != original_time

    @pytest.mark.asyncio
    async def test_json_attributes(self, db: DatabaseManager):
        """测试 JSON 属性存储."""
        await db.initialize()

        import json

        attrs = {"strength": 10, "dexterity": 15, "inventory": ["sword", "shield"]}

        cursor = await db.execute(
            "INSERT INTO objects (key, typeclass_path, attributes) VALUES (?, ?, ?)",
            ("hero", "src.game.Character", json.dumps(attrs)),
        )
        await db.commit()
        obj_id = cursor.lastrowid

        row = await db.fetchone(
            "SELECT attributes FROM objects WHERE id = ?",
            (obj_id,),
        )
        loaded_attrs = json.loads(row["attributes"])
        assert loaded_attrs["strength"] == 10
        assert loaded_attrs["inventory"] == ["sword", "shield"]

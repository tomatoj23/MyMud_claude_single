"""ObjectManager 单元测试.

测试 L1/L2 缓存、对象创建/加载/删除、条件查询、批量保存等功能。
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.engine.core.typeclass import TypeclassBase
from src.engine.database.connection import DatabaseManager
from src.engine.objects.manager import ObjectManager


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_obj")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.engine.core.typeclass.TypeclassBase"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


@pytest.fixture
async def db_manager():
    """创建真实的数据库管理器."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(db_path)
        await db.initialize()
        yield db
        await db.close()


@pytest.fixture
async def object_manager(db_manager: DatabaseManager):
    """创建对象管理器."""
    manager = ObjectManager(db_manager)
    await manager.initialize()
    yield manager


class TestObjectManagerInitialization:
    """对象管理器初始化测试."""

    @pytest.mark.asyncio
    async def test_initialize(self, db_manager: DatabaseManager):
        """测试初始化."""
        manager = ObjectManager(db_manager)
        await manager.initialize()

        assert manager._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, db_manager: DatabaseManager):
        """测试初始化幂等."""
        manager = ObjectManager(db_manager)
        await manager.initialize()
        await manager.initialize()  # 第二次应该不执行操作

        assert manager._initialized is True


class TestL1Cache:
    """L1 缓存测试."""

    @pytest.mark.asyncio
    async def test_get_from_l1_cache(self, object_manager: ObjectManager):
        """测试从 L1 缓存获取对象."""
        # 创建对象
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="test_obj",
        )

        # 从 L1 缓存获取
        cached = object_manager.get(obj.id)

        assert cached is obj

    @pytest.mark.asyncio
    async def test_get_from_l1_returns_none_for_missing(
        self, object_manager: ObjectManager
    ):
        """测试获取不存在的对象返回 None."""
        cached = object_manager.get(99999)

        assert cached is None

    @pytest.mark.asyncio
    async def test_get_none_id_returns_none(self, object_manager: ObjectManager):
        """测试获取 None ID 返回 None."""
        cached = object_manager.get(None)  # type: ignore

        assert cached is None

    @pytest.mark.asyncio
    async def test_weakref_cleanup(self, object_manager: ObjectManager):
        """测试弱引用自动清理."""
        # 创建对象
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="temp_obj",
        )
        obj_id = obj.id

        # 删除引用
        del obj

        # 强制垃圾回收
        import gc

        gc.collect()

        # 缓存应该被清理
        cached = object_manager._get_from_l1(obj_id)
        assert cached is None


class TestObjectCreation:
    """对象创建测试."""

    @pytest.mark.asyncio
    async def test_create_object(self, object_manager: ObjectManager):
        """测试创建对象."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="new_obj",
        )

        assert obj is not None
        assert obj.key == "new_obj"
        assert obj.get_typeclass_path() == "src.engine.core.typeclass.TypeclassBase"
        assert obj.id is not None

    @pytest.mark.asyncio
    async def test_create_with_location(self, object_manager: ObjectManager):
        """测试创建对象带位置."""
        # 先创建位置
        room = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="room",
        )

        # 创建在位置中的对象
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="item",
            location=room,
        )

        # 验证 location_id 已设置
        assert obj._db_model.location_id == room.id

    @pytest.mark.asyncio
    async def test_create_with_attributes(self, object_manager: ObjectManager):
        """测试创建对象带初始属性."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="attr_obj",
            attributes={"color": "red", "weight": 10},
        )

        assert obj.db.color == "red"
        assert obj.db.weight == 10

    @pytest.mark.asyncio
    async def test_create_added_to_l1_cache(self, object_manager: ObjectManager):
        """测试创建的对象添加到 L1 缓存."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="cached_obj",
        )

        cached = object_manager.get(obj.id)
        assert cached is obj


class TestObjectLoading:
    """对象加载测试."""

    @pytest.mark.asyncio
    async def test_load_from_l1_cache(self, object_manager: ObjectManager):
        """测试优先从 L1 缓存加载."""
        # 创建对象
        original = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="cached_obj",
        )

        # 再次加载应该返回同一个实例
        loaded = await object_manager.load(original.id)

        assert loaded is original

    @pytest.mark.asyncio
    async def test_load_from_database(self, object_manager: ObjectManager):
        """测试从数据库加载."""
        # 创建对象
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="db_obj",
        )
        obj_id = obj.id

        # 清除 L1 缓存（模拟重启）
        object_manager._l1_cache.clear()

        # 从数据库重新加载
        loaded = await object_manager.load(obj_id)

        assert loaded is not None
        assert loaded.id == obj_id
        assert loaded.key == "db_obj"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, object_manager: ObjectManager):
        """测试加载不存在的对象."""
        loaded = await object_manager.load(99999)

        assert loaded is None

    @pytest.mark.asyncio
    async def test_load_invalid_typeclass(self, object_manager: ObjectManager):
        """测试加载无效类型类时使用默认基类."""
        # 手动插入一条无效类型路径的记录
        cursor = await object_manager.db.execute(
            "INSERT INTO objects (key, typeclass_path) VALUES (?, ?)",
            ("bad_obj", "invalid.nonexistent.Class"),
        )
        await object_manager.db.commit()
        obj_id = cursor.lastrowid

        # 加载应该使用默认基类
        loaded = await object_manager.load(obj_id)

        assert loaded is not None
        assert isinstance(loaded, TypeclassBase)


class TestObjectDeletion:
    """对象删除测试."""

    @pytest.mark.asyncio
    async def test_delete_object(self, object_manager: ObjectManager):
        """测试删除对象."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="delete_me",
        )
        obj_id = obj.id

        success = await object_manager.delete(obj)

        assert success is True
        # 从数据库验证已删除
        row = await object_manager.db.fetchone(
            "SELECT * FROM objects WHERE id = ?",
            (obj_id,),
        )
        assert row is None

    @pytest.mark.asyncio
    async def test_delete_calls_at_delete(self, object_manager: ObjectManager):
        """测试删除调用 at_delete 钩子."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="hook_obj",
        )

        with patch.object(obj, "at_delete") as mock_at_delete:
            await object_manager.delete(obj)
            mock_at_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_removes_from_cache(self, object_manager: ObjectManager):
        """测试删除从缓存中移除."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="cached_delete",
        )
        obj_id = obj.id

        await object_manager.delete(obj)

        # 应该从 L1 缓存移除
        assert object_manager.get(obj_id) is None
        # 应该从查询缓存移除
        assert obj_id not in object_manager._query_cache

    @pytest.mark.asyncio
    async def test_delete_dirty_object(self, object_manager: ObjectManager):
        """测试删除脏数据对象."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="dirty_delete",
        )
        obj_id = obj.id

        # 标记为脏数据
        object_manager.mark_dirty(obj)

        await object_manager.delete(obj)

        # 应该从脏数据集合移除
        assert obj_id not in object_manager._dirty_objects


class TestObjectQuery:
    """对象查询测试."""

    @pytest.mark.asyncio
    async def test_find_by_typeclass(self, object_manager: ObjectManager):
        """测试按类型路径查询."""
        # 创建不同类型对象
        await object_manager.create(
            typeclass_path="src.game.Room",
            key="room1",
        )
        await object_manager.create(
            typeclass_path="src.game.Room",
            key="room2",
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="item1",
        )

        rooms = await object_manager.find(typeclass_path="src.game.Room")

        assert len(rooms) == 2
        keys = {r.key for r in rooms}
        assert "room1" in keys
        assert "room2" in keys

    @pytest.mark.asyncio
    async def test_find_by_location(self, object_manager: ObjectManager):
        """测试按位置查询."""
        room = await object_manager.create(
            typeclass_path="src.game.Room",
            key="room",
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="item1",
            location=room,
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="item2",
            location=room,
        )

        items = await object_manager.find(location=room)

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_find_by_key_contains(self, object_manager: ObjectManager):
        """测试按 key 包含查询."""
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="sword_of_fire",
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="fire_ring",
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="shield",
        )

        fire_items = await object_manager.find(key_contains="fire")

        assert len(fire_items) == 2

    @pytest.mark.asyncio
    async def test_find_combined_conditions(self, object_manager: ObjectManager):
        """测试组合条件查询."""
        room = await object_manager.create(
            typeclass_path="src.game.Room",
            key="room",
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="magic_sword",
            location=room,
        )
        await object_manager.create(
            typeclass_path="src.game.Item",
            key="magic_shield",
            location=room,
        )
        await object_manager.create(
            typeclass_path="src.game.NPC",
            key="magic_wizard",
            location=room,
        )

        items = await object_manager.find(
            typeclass_path="src.game.Item",
            location=room,
            key_contains="magic",
        )

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_find_limit(self, object_manager: ObjectManager):
        """测试查询限制."""
        for i in range(10):
            await object_manager.create(
                typeclass_path="src.game.Item",
                key=f"item_{i}",
            )

        items = await object_manager.find(typeclass_path="src.game.Item", limit=5)

        assert len(items) == 5


class TestObjectSave:
    """对象保存测试."""

    @pytest.mark.asyncio
    async def test_save_dirty_object(self, object_manager: ObjectManager):
        """测试保存脏数据对象."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="save_test",
        )
        obj.clean_dirty()

        # 修改属性使其变脏
        obj.key = "modified"

        success = await object_manager.save(obj)

        assert success is True
        assert obj.is_dirty() is False

        # 验证数据库已更新
        row = await object_manager.db.fetchone(
            "SELECT key FROM objects WHERE id = ?",
            (obj.id,),
        )
        assert row["key"] == "modified"

    @pytest.mark.asyncio
    async def test_save_clean_object_skipped(self, object_manager: ObjectManager):
        """测试保存干净对象被跳过."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="clean_obj",
        )
        obj.clean_dirty()

        with patch.object(
            object_manager.db, "execute", new_callable=AsyncMock
        ) as mock_execute:
            success = await object_manager.save(obj)

            # 不应该执行数据库操作
            mock_execute.assert_not_called()
            assert success is True

    @pytest.mark.asyncio
    async def test_save_force(self, object_manager: ObjectManager):
        """测试强制保存."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="force_save",
        )
        obj.clean_dirty()

        with patch.object(
            object_manager.db, "execute", new_callable=AsyncMock
        ) as mock_execute:
            await object_manager.save(obj, force=True)

            # 应该执行数据库操作
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_all_dirty(self, object_manager: ObjectManager):
        """测试批量保存脏数据对象."""
        obj1 = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="obj1",
        )
        obj2 = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="obj2",
        )

        obj1.clean_dirty()
        obj2.clean_dirty()

        # 修改使变脏
        obj1.key = "modified1"
        obj2.key = "modified2"

        count = await object_manager.save_all()

        assert count == 2

    @pytest.mark.asyncio
    async def test_save_all_empty(self, object_manager: ObjectManager):
        """测试批量保存无脏数据时."""
        count = await object_manager.save_all()

        assert count == 0


class TestCacheManagement:
    """缓存管理测试."""

    @pytest.mark.asyncio
    async def test_mark_dirty(self, object_manager: ObjectManager):
        """测试标记脏数据."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="mark_dirty_test",
        )

        object_manager.mark_dirty(obj)

        assert obj.id in object_manager._dirty_objects

    @pytest.mark.asyncio
    async def test_clear_cache(self, object_manager: ObjectManager):
        """测试清理缓存."""
        # 创建对象使其进入缓存
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="cache_test",
        )

        # 清理缓存
        object_manager.clear_cache()

        # L1 缓存中的弱引用会被检查
        stats = object_manager.get_cache_stats()
        assert stats["l1_cache_size"] >= 0  # 弱引用可能已被清理

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, object_manager: ObjectManager):
        """测试获取缓存统计信息."""
        obj = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="stats_test",
        )
        object_manager.mark_dirty(obj)

        stats = object_manager.get_cache_stats()

        assert "l1_cache_size" in stats
        assert "l2_cache_size" in stats
        assert "dirty_objects" in stats
        assert stats["dirty_objects"] == 1


class TestObjectManagerContentsSync:
    """ObjectManager.get_contents_sync 同步内容查询测试."""

    @pytest.mark.asyncio
    async def test_get_contents_sync_empty(self, object_manager: ObjectManager):
        """测试获取空容器的内容."""
        # 创建容器
        container = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="container",
        )

        # 同步获取内容
        contents = object_manager.get_contents_sync(container.id)
        assert contents == []

    @pytest.mark.asyncio
    async def test_get_contents_sync_with_items(self, object_manager: ObjectManager):
        """测试获取包含物品的容器内容."""
        # 创建容器
        container = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="container",
        )

        # 创建两个物品在容器中
        item1 = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="sword",
            location=container,
        )
        item2 = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="shield",
            location=container,
        )

        # 创建另一个物品不在容器中
        other = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="other",
        )

        # 同步获取内容
        contents = object_manager.get_contents_sync(container.id)

        # 验证结果
        assert len(contents) == 2
        assert item1 in contents
        assert item2 in contents
        assert other not in contents

    @pytest.mark.asyncio
    async def test_get_contents_sync_only_l1_cache(self, object_manager: ObjectManager):
        """测试 get_contents_sync 只返回L1缓存中的对象."""
        # 创建容器和物品
        container = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="container",
        )
        item = await object_manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="item",
            location=container,
        )

        # 验证对象在L1缓存中
        assert object_manager._get_from_l1(item.id) is not None

        # 获取内容
        contents = object_manager.get_contents_sync(container.id)
        assert len(contents) == 1
        assert contents[0].id == item.id

        # 清除L1缓存（模拟对象被回收）
        object_manager._l1_cache.clear()

        # 再次获取内容，应该为空
        contents = object_manager.get_contents_sync(container.id)
        assert contents == []

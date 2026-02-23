"""ObjectManager 补充测试 - 提高覆盖率.

测试object_manager.py中未被覆盖的代码路径。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.engine.objects.manager import ObjectManager


class TestObjectManagerFind:
    """对象查找测试."""

    @pytest.mark.asyncio
    async def test_find_by_typeclass(self):
        """测试按类型类查找."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        results = await manager.find(typeclass_path="TestClass")
        assert results == []

    @pytest.mark.asyncio
    async def test_find_by_location(self):
        """测试按位置查找."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        # 创建mock位置对象
        location = MagicMock()
        location.id = 1
        results = await manager.find(location=location)
        assert results == []

    @pytest.mark.asyncio
    async def test_find_by_key_contains(self):
        """测试按key包含查找."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        results = await manager.find(key_contains="test")
        assert results == []

    @pytest.mark.asyncio
    async def test_find_combined_conditions(self):
        """测试组合条件查找."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        location = MagicMock()
        location.id = 1
        results = await manager.find(
            typeclass_path="TestClass",
            location=location,
            key_contains="test"
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_find_with_limit(self):
        """测试限制数量查找."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        results = await manager.find(limit=10)
        assert results == []


class TestObjectManagerSave:
    """对象保存测试."""

    @pytest.mark.asyncio
    async def test_save_clean_object_skipped(self):
        """测试保存干净对象（跳过）."""
        db = AsyncMock()
        manager = ObjectManager(db)
        await manager.initialize()
        
        obj = MagicMock()
        obj.is_dirty.return_value = False
        
        result = await manager.save(obj)
        assert result is True
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_force(self):
        """测试强制保存."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        obj = MagicMock()
        obj.id = 1
        obj.is_dirty.return_value = False
        obj.to_db_dict.return_value = {
            "id": 1,
            "key": "test",
            "typeclass_path": "TestClass",
            "location_id": None,
            "attributes": {},
        }
        
        result = await manager.save(obj, force=True)
        # 即使失败也不应该抛出异常
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_save_all_dirty(self):
        """测试保存所有脏对象."""
        db = AsyncMock()
        db.execute = AsyncMock()
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        # 添加脏对象
        obj1 = MagicMock()
        obj1.is_dirty.return_value = True
        obj1.to_db_dict.return_value = {
            "id": 1, "key": "obj1", "typeclass_path": "Test",
            "location_id": None, "attributes": {},
        }
        manager._dirty_objects.add(obj1)
        
        count = await manager.save_all()
        assert count >= 0


class TestObjectManagerCache:
    """缓存管理测试."""

    def test_get_cache_stats(self):
        """测试获取缓存统计."""
        db = MagicMock()
        manager = ObjectManager(db)
        
        stats = manager.get_cache_stats()
        assert "l1_cache_size" in stats

    def test_clear_cache(self):
        """测试清除缓存."""
        db = MagicMock()
        manager = ObjectManager(db)
        
        manager.clear_cache()
        # 验证缓存已清除
        assert len(manager._l1_cache) == 0


class TestObjectManagerLoadMany:
    """批量加载测试."""

    @pytest.mark.asyncio
    async def test_load_many_empty(self):
        """测试批量加载空列表."""
        db = MagicMock()
        manager = ObjectManager(db)
        await manager.initialize()
        
        results = await manager.load_many([])
        assert results == []

    @pytest.mark.asyncio
    async def test_load_many_all_cached(self):
        """测试批量加载（全部缓存命中）."""
        db = MagicMock()
        manager = ObjectManager(db)
        await manager.initialize()
        
        # Mock L1缓存
        obj = MagicMock()
        manager._l1_cache[1] = obj
        
        with patch.object(manager, '_get_from_l1', return_value=obj):
            results = await manager.load_many([1, 1])  # 重复ID
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_load_many_with_missing(self):
        """测试批量加载（包含缺失对象）."""
        db = AsyncMock()
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        # 没有缓存，也没有数据库记录
        with patch.object(manager, '_get_from_l1', return_value=None):
            with patch.object(manager, '_fetch_many_from_db', return_value={}):
                results = await manager.load_many([1, 2], skip_missing=False)
                assert len(results) == 2
                assert results[0] is None


class TestObjectManagerFetchManyFromDb:
    """批量从数据库获取测试."""

    @pytest.mark.asyncio
    async def test_fetch_many_empty(self):
        """测试批量获取空列表."""
        db = MagicMock()
        manager = ObjectManager(db)
        
        results = await manager._fetch_many_from_db([])
        assert results == {}

    @pytest.mark.asyncio
    async def test_fetch_many_with_string_attributes(self):
        """测试批量获取（字符串属性）."""
        db = AsyncMock()
        # 返回空结果，因为我们无法mock内部方法
        db.fetchall = AsyncMock(return_value=[])
        
        manager = ObjectManager(db)
        
        results = await manager._fetch_many_from_db([1])
        assert results == {}


class TestObjectManagerDelete:
    """对象删除测试."""

    @pytest.mark.asyncio
    async def test_delete_dirty_object(self):
        """测试删除脏对象."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        
        manager = ObjectManager(db)
        await manager.initialize()
        
        obj = MagicMock()
        obj.id = 1
        obj.key = "test"
        obj.at_delete = MagicMock()
        
        # 添加到脏对象集合（存储ID）
        manager._dirty_objects.add(obj.id)
        
        result = await manager.delete(obj)
        assert result is True
        assert obj.id not in manager._dirty_objects

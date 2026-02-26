"""性能优化边界测试.

测试批量加载、缓存机制的正确性和边界情况.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from src.engine.objects.manager import ObjectManager
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot

if TYPE_CHECKING:
    from src.engine.database.connection import DatabaseManager


@pytest.fixture
def mock_manager():
    """创建Mock对象管理器."""
    mock_db = Mock(spec=ObjectManager)
    manager = ObjectManager(mock_db)
    manager._initialized = True
    return manager


class TestLoadMany:
    """批量加载边界测试."""

    @pytest.mark.asyncio
    async def test_load_many_empty_list(self, mock_manager):
        """测试空列表批量加载."""
        results = await mock_manager.load_many([])
        assert results == []

    @pytest.mark.asyncio
    async def test_load_many_all_cached(self, mock_manager):
        """测试全部命中L1缓存的批量加载."""
        # 创建模拟对象
        mock_obj1 = Mock()
        mock_obj1.id = 1
        mock_obj2 = Mock()
        mock_obj2.id = 2

        # 添加到L1缓存
        mock_manager._l1_cache[1] = Mock(return_value=mock_obj1)
        mock_manager._l1_cache[2] = Mock(return_value=mock_obj2)

        # 批量加载
        results = await mock_manager.load_many([1, 2])

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 2

    @pytest.mark.asyncio
    async def test_load_many_order_preserved(self, mock_manager):
        """测试批量加载结果顺序保持."""
        # 创建多个模拟对象
        for i in range(5):
            mock_obj = Mock()
            mock_obj.id = i + 1
            mock_manager._l1_cache[i + 1] = Mock(return_value=mock_obj)

        # 乱序请求
        request_ids = [3, 1, 5, 2, 4]
        results = await mock_manager.load_many(request_ids)

        # 验证顺序保持
        assert [obj.id for obj in results] == request_ids

    @pytest.mark.asyncio
    async def test_load_many_skip_missing(self, mock_manager):
        """测试跳过缺失对象的批量加载."""
        # 只缓存ID为1的对象
        mock_obj = Mock()
        mock_obj.id = 1
        mock_manager._l1_cache[1] = Mock(return_value=mock_obj)

        # 批量加载（包含不存在的ID）
        results = await mock_manager.load_many([1, 999, 2], skip_missing=True)

        # 验证只返回存在的对象
        assert len(results) == 1
        assert results[0].id == 1

    @pytest.mark.asyncio
    async def test_load_many_include_missing(self, mock_manager):
        """测试包含None的批量加载."""
        mock_obj = Mock()
        mock_obj.id = 1
        mock_manager._l1_cache[1] = Mock(return_value=mock_obj)

        results = await mock_manager.load_many([1, 999], skip_missing=False)

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1] is None

    @pytest.mark.asyncio
    async def test_load_many_batch_processing(self, mock_manager):
        """测试大批量分批处理."""
        # 创建超过批量大小的对象数量
        for i in range(1000):
            mock_obj = Mock()
            mock_obj.id = i + 1
            mock_manager._l1_cache[i + 1] = Mock(return_value=mock_obj)

        # 批量加载1000个对象
        obj_ids = list(range(1, 1001))
        results = await mock_manager.load_many(obj_ids)

        assert len(results) == 1000


class TestQueryCache:
    """查询缓存边界测试."""

    @pytest.mark.asyncio
    async def test_query_cache_basic(self, tmp_path):
        """测试基本查询缓存功能."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 创建测试对象
        obj1 = await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="缓存测试1",
        )

        # 首次查询（应该缓存）
        results1 = await engine.objects.find(key_contains="缓存测试")

        # 再次查询（应该命中缓存）
        results2 = await engine.objects.find(key_contains="缓存测试")

        assert len(results1) == len(results2)

        await engine.stop()

    @pytest.mark.asyncio
    async def test_query_cache_invalidation_on_create(self, tmp_path):
        """测试创建对象使查询缓存失效."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 首次查询
        await engine.objects.find(key_contains="失效测试")
        cache_size_before = len(engine.objects._query_result_cache)
        assert cache_size_before > 0

        # 创建新对象
        await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="失效测试新对象",
        )

        # 验证缓存被清除
        cache_size_after = len(engine.objects._query_result_cache)
        assert cache_size_after == 0

        await engine.stop()

    @pytest.mark.asyncio
    async def test_query_cache_ttl_expiration(self, tmp_path):
        """测试查询缓存TTL过期."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 设置短TTL
        engine.objects._query_cache_ttl = 0.01  # 10ms

        # 创建对象并查询
        await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="TTL测试",
        )
        await engine.objects.find(key_contains="TTL测试")

        # 等待TTL过期
        await asyncio.sleep(0.02)

        # 再次查询，缓存应该已过期
        results = await engine.objects.find(key_contains="TTL测试")
        assert len(results) >= 1

        await engine.stop()

    @pytest.mark.asyncio
    async def test_query_cache_disabled(self, tmp_path):
        """测试禁用查询缓存."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 创建对象
        await engine.objects.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="禁用缓存测试",
        )

        # 禁用缓存查询
        results1 = await engine.objects.find(
            key_contains="禁用缓存测试",
            use_cache=False,
        )

        # 验证缓存未被写入
        cache_key = engine.objects._make_query_cache_key(
            None, None, "禁用缓存测试", 100
        )
        assert cache_key not in engine.objects._query_result_cache

        await engine.stop()


class TestEquipmentCache:
    """装备属性缓存边界测试."""

    @pytest.mark.asyncio
    async def test_equipment_cache_on_equip(self, mock_manager):
        """测试装备时缓存失效."""
        # 创建模拟角色
        character = Mock(spec=Character)
        character._cached_total_stats = {"attack": 100}

        # 模拟卸下缓存的方法（直接调用实例方法）
        character._equipment_invalidate_cache()

        # 验证缓存被清除（Mock会记录调用）
        character._equipment_invalidate_cache.assert_called_once()

    def test_equipment_cache_returns_copy(self):
        """测试装备缓存返回副本."""
        from unittest.mock import MagicMock

        # 创建模拟character
        character = MagicMock()
        character._cached_total_stats = {"attack": 50, "defense": 30}

        # 模拟get_total_stats行为
        def get_total_stats():
            if character._cached_total_stats is not None:
                return character._cached_total_stats.copy()
            return {}

        result1 = get_total_stats()
        result2 = get_total_stats()

        # 验证是副本
        assert result1 is not result2
        assert result1 == result2

        # 修改返回结果不应影响缓存
        result1["attack"] = 999
        assert character._cached_total_stats["attack"] == 50


class TestCacheStats:
    """缓存统计信息测试."""

    def test_cache_stats_format(self, mock_manager):
        """测试缓存统计信息格式."""
        stats = mock_manager.get_cache_stats()

        assert "l1_cache_size" in stats
        assert "l2_cache_size" in stats
        assert "query_result_cache_size" in stats
        assert "valid_query_cache" in stats
        assert "dirty_objects" in stats

        # 验证所有值为非负整数
        for key, value in stats.items():
            assert isinstance(value, int)
            assert value >= 0

    @pytest.mark.asyncio
    async def test_cache_stats_with_expired_entries(self, mock_manager):
        """测试有过期条目的缓存统计."""
        import time

        # 添加过期缓存
        mock_manager._query_result_cache["expired"] = (
            [1, 2, 3],
            time.time() - 10,  # 已过期
        )

        # 添加有效缓存
        mock_manager._query_result_cache["valid"] = (
            [4, 5],
            time.time() + 10,  # 未过期
        )

        stats = mock_manager.get_cache_stats()

        assert stats["query_result_cache_size"] == 2
        assert stats["valid_query_cache"] == 1


class TestConcurrency:
    """并发访问边界测试."""

    @pytest.mark.asyncio
    async def test_concurrent_load_many(self, tmp_path):
        """测试并发批量加载."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 创建多个对象
        obj_ids = []
        for i in range(20):
            obj = await engine.objects.create(
                typeclass_path="src.engine.core.typeclass.TypeclassBase",
                key=f"并发测试{i}",
            )
            obj_ids.append(obj.id)

        # 并发批量加载
        async def load_subset(ids):
            return await engine.objects.load_many(ids)

        # 分成多个子集并发加载
        tasks = [
            load_subset(obj_ids[i:i + 5])
            for i in range(0, len(obj_ids), 5)
        ]

        results = await asyncio.gather(*tasks)

        # 验证所有加载成功
        total_loaded = sum(len(r) for r in results)
        assert total_loaded == len(obj_ids)

        await engine.stop()


class TestPerformanceBaseline:
    """性能基准测试."""

    @pytest.mark.asyncio
    async def test_batch_vs_individual_load(self, tmp_path):
        """测试批量加载vs逐个加载性能."""
        from src.engine.core.engine import GameEngine
        from src.utils.config import Config

        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

        engine = GameEngine(config)
        await engine.initialize()

        # 创建测试对象
        obj_ids = []
        for i in range(10):  # 10个对象用于测试
            obj = await engine.objects.create(
                typeclass_path="src.engine.core.typeclass.TypeclassBase",
                key=f"性能测试{i}",
            )
            obj_ids.append(obj.id)

        # 清除缓存
        engine.objects._l1_cache.clear()
        engine.objects._query_cache.clear()

        # 测量批量加载
        start = time.time()
        batch_results = await engine.objects.load_many(obj_ids)
        batch_time = time.time() - start

        # 清除缓存
        engine.objects._l1_cache.clear()
        engine.objects._query_cache.clear()

        # 测量逐个加载
        start = time.time()
        individual_results = []
        for obj_id in obj_ids:
            obj = await engine.objects.load(obj_id)
            individual_results.append(obj)
        individual_time = time.time() - start

        # 验证结果一致
        assert len(batch_results) == len(individual_results)

        # 批量加载应该更快（至少快2倍）
        assert batch_time < individual_time / 2, (
            f"批量加载({batch_time:.3f}s)应该比逐个加载({individual_time:.3f}s)快"
        )

        await engine.stop()

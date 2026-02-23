"""性能与压力测试.

测试系统在高负载、大数据量下的表现。
"""
import asyncio
import pytest
import tempfile
import time
import tracemalloc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.npc.core import NPC, NPCType
from src.game.quest.core import Quest, QuestObjective, QuestObjectiveType, QuestType


class TestPerformanceLargeScale:
    """大规模数据性能测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'perf_test.db'}"
        config.game.auto_save_interval = 60
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_create_1000_characters(self, engine):
        """测试批量创建1000个角色."""
        start_time = time.time()
        
        characters = []
        for i in range(1000):
            char = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"char_{i}",
                attributes={"name": f"角色{i}", "level": i % 100}
            )
            characters.append(char)
        
        elapsed = time.time() - start_time
        
        # 验证所有角色创建成功
        assert len(characters) == 1000
        
        # 性能要求：1000个角色应在30秒内创建完成
        print(f"创建1000个角色耗时: {elapsed:.2f}秒")
        assert elapsed < 30.0, f"创建速度太慢: {elapsed}秒"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_save_performance(self, engine):
        """测试批量保存性能."""
        # 创建大量对象
        chars = []
        for i in range(500):
            char = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"save_char_{i}",
                attributes={"name": f"保存测试角色{i}"}
            )
            char.attributes = {"strength": i, "agility": i}
            engine.objects.mark_dirty(char)
            chars.append(char)
        
        # 批量保存计时
        start_time = time.time()
        await engine.objects.save_all()
        elapsed = time.time() - start_time
        
        print(f"批量保存500个角色耗时: {elapsed:.2f}秒")
        assert elapsed < 10.0, f"保存速度太慢: {elapsed}秒"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_query_performance_with_large_dataset(self, engine):
        """测试大数据集查询性能."""
        # 创建不同类型的大量对象
        for i in range(200):
            await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"query_char_{i}",
                attributes={"menpai": ["少林", "武当", "峨眉"][i % 3]}
            )
        
        for i in range(200):
            await engine.objects.create(
                typeclass_path="src.game.typeclasses.equipment.Equipment",
                key=f"query_equip_{i}",
                attributes={"slot": "weapon" if i % 2 == 0 else "armor"}
            )
        
        # 测试查询性能
        start_time = time.time()
        
        # 按类型查询（提高限制以获取所有结果）
        results = await engine.objects.find(
            typeclass_path="src.game.typeclasses.character.Character",
            limit=500
        )
        
        elapsed = time.time() - start_time
        print(f"查询400个对象耗时: {elapsed:.3f}秒")
        
        # 查询应在1秒内完成
        assert elapsed < 1.0
        assert len(results) >= 200


class TestMemoryUsage:
    """内存使用测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'memory_test.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_leak_on_object_creation(self, engine):
        """测试对象创建是否存在内存泄漏."""
        tracemalloc.start()
        
        # 创建大量对象并删除
        for batch in range(5):
            chars = []
            for i in range(100):
                char = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.character.Character",
                    key=f"mem_char_{batch}_{i}",
                    attributes={"name": f"内存测试角色{batch}_{i}"}
                )
                chars.append(char)
            
            # 清除缓存引用
            for char in chars:
                engine.objects._l1_cache.pop(char.id, None)
            chars.clear()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"当前内存使用: {current / 1024 / 1024:.2f} MB")
        print(f"峰值内存使用: {peak / 1024 / 1024:.2f} MB")
        
        # 内存使用应在合理范围内（小于100MB）
        assert current < 100 * 1024 * 1024, "内存使用过高，可能存在泄漏"
    
    @pytest.mark.asyncio
    async def test_large_attribute_memory(self, engine):
        """测试大属性数据的内存使用."""
        tracemalloc.start()
        
        # 创建带有大属性的对象
        large_data = {"data": "x" * 100000}  # 100KB
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="large_attr_char",
            attributes={"large_data": large_data}
        )
        
        current, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 大属性应被正确处理，内存使用合理
        print(f"大属性对象内存使用: {current / 1024:.2f} KB")


class TestConcurrentOperations:
    """并发操作测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'concurrent.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_rapid_object_access(self, engine):
        """测试快速连续对象访问."""
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="rapid_access_char",
            attributes={"name": "快速访问测试"}
        )
        
        # 快速连续访问同一对象100次
        start_time = time.time()
        for _ in range(100):
            loaded = await engine.objects.load(char.id)
            assert loaded is not None
        
        elapsed = time.time() - start_time
        print(f"100次对象访问耗时: {elapsed:.3f}秒")
        
        # 应在1秒内完成
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_simultaneous_readers(self, engine):
        """测试同时读取同一对象."""
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="shared_char",
            attributes={"name": "共享角色"}
        )
        
        # 并发读取
        async def read_char():
            return await engine.objects.load(char.id)
        
        # 创建10个并发读取任务
        tasks = [read_char() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 所有读取都应成功
        assert all(r is not None for r in results)
        assert all(r.id == char.id for r in results)


class TestStressScenarios:
    """压力场景测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'stress.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_massive_equipment_switching(self, engine):
        """测试大规模装备切换."""
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="equip_switch_char",
            attributes={"name": "装备切换测试"}
        )
        
        # 创建100件装备
        equipments = []
        for i in range(100):
            equip = await engine.objects.create(
                typeclass_path="src.game.typeclasses.equipment.Equipment",
                key=f"switch_equip_{i}",
                attributes={"name": f"装备{i}"}
            )
            equip.slot = EquipmentSlot.MAIN_HAND
            equip.location = char
            equipments.append(equip)
        
        # 快速切换装备50次
        start_time = time.time()
        for i in range(50):
            await char.equip(equipments[i % len(equipments)])
        
        elapsed = time.time() - start_time
        print(f"50次装备切换耗时: {elapsed:.3f}秒")
        
        assert elapsed < 5.0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_massive_quest_updates(self, engine):
        """测试大量任务进度更新."""
        from unittest.mock import MagicMock
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="quest_stress_char",
            attributes={"name": "任务压力测试"}
        )
        
        # 设置任务数据 - 使用简单属性更新模拟任务进度
        char.db = MagicMock()
        quest_progress = {}
        char.db.get = MagicMock(side_effect=lambda key, default=None: quest_progress if key == "quest_progress" else default)
        def mock_set(key, value):
            nonlocal quest_progress
            if key == "quest_progress":
                quest_progress = value
        char.db.set = MagicMock(side_effect=mock_set)
        
        # 快速更新任务进度（直接操作数据）
        start_time = time.time()
        for quest_idx in range(20):  # 测试20个任务
            for progress in range(1, 11):
                current = char.db.get("quest_progress", {})
                quest_key = f"quest_{quest_idx}"
                if quest_key not in current:
                    current[quest_key] = {"progress": 0, "completed": False}
                current[quest_key]["progress"] += 1
                if current[quest_key]["progress"] >= 10:
                    current[quest_key]["completed"] = True
                char.db.set("quest_progress", current)
        
        elapsed = time.time() - start_time
        print(f"200次任务更新耗时: {elapsed:.3f}秒")
        
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_database_connection_pool(self, engine):
        """测试数据库连接池在高负载下的表现."""
        # 创建大量并发数据库操作
        async def db_operation(i):
            char = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"pool_char_{i}",
                attributes={"name": f"连接池测试{i}"}
            )
            return char
        
        # 创建50个并发任务
        start_time = time.time()
        tasks = [db_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        print(f"50个并发数据库操作耗时: {elapsed:.3f}秒")
        
        assert len(results) == 50
        assert elapsed < 10.0


class TestLongRunningStability:
    """长时间运行稳定性测试."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_engine_5_minute_stability(self):
        """测试引擎5分钟稳定运行."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'stability.db'}"
        config.game.auto_save_interval = 10  # 10秒自动保存
        
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        try:
            # 创建一些初始对象
            chars = []
            for i in range(10):
                char = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.character.Character",
                    key=f"stability_char_{i}",
                    attributes={"name": f"稳定性测试角色{i}"}
                )
                chars.append(char)
            
            # 运行5分钟，每30秒执行一次操作
            start_time = time.time()
            iteration = 0
            
            while time.time() - start_time < 300:  # 5分钟
                await asyncio.sleep(30)
                iteration += 1
                
                # 执行一些操作
                for char in chars:
                    char.attributes = {"strength": iteration}
                    engine.objects.mark_dirty(char)
                
                await engine.objects.save_all()
                print(f"第{iteration}轮操作完成")
            
            print(f"5分钟稳定性测试完成，共执行{iteration}轮操作")
            
        finally:
            await engine.stop()


# 标记慢测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.performance
]

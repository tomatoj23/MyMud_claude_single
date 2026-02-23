"""核心模块性能基准测试.

测试关键操作的性能指标.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from benchmarks import async_benchmark, benchmark
from src.engine.core.engine import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.typeclasses.room import Room
from src.utils.config import Config


class TestObjectManagerPerformance:
    """对象管理器性能测试."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_create_object_performance(self):
        """测试对象创建性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            result = await async_benchmark(
                "对象创建",
                lambda: engine.objects.create(
                    typeclass_path="src.engine.core.typeclass.TypeclassBase",
                    key="perf_test",
                ),
                iterations=50,
                warmup=5,
            )
            
            print(f"\n{result}")
            # 断言：平均创建时间应小于100ms
            assert result.avg_time < 0.1
            
            await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_load_many_performance(self):
        """测试批量加载性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            # 创建测试对象
            obj_ids = []
            for i in range(20):
                obj = await engine.objects.create(
                    typeclass_path="src.engine.core.typeclass.TypeclassBase",
                    key=f"batch_test_{i}",
                )
                obj_ids.append(obj.id)
            
            # 清除缓存
            engine.objects._l1_cache.clear()
            engine.objects._query_cache.clear()
            
            result = await async_benchmark(
                "批量加载20个对象",
                lambda: engine.objects.load_many(obj_ids),
                iterations=20,
                warmup=3,
            )
            
            print(f"\n{result}")
            # 断言：批量加载20个对象应小于50ms
            assert result.avg_time < 0.05
            
            await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_find_performance(self):
        """测试查询性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            # 创建测试对象
            for i in range(50):
                await engine.objects.create(
                    typeclass_path="src.engine.core.typeclass.TypeclassBase",
                    key=f"find_test_{i}",
                )
            
            result = await async_benchmark(
                "查询50个对象",
                lambda: engine.objects.find(key_contains="find_test"),
                iterations=20,
                warmup=3,
            )
            
            print(f"\n{result}")
            # 断言：查询应小于30ms
            assert result.avg_time < 0.03
            
            await engine.stop()


class TestCharacterPerformance:
    """角色操作性能测试."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_character_status_calculation(self):
        """测试角色状态计算性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            character = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key="perf_char",
                attributes={
                    "birth_talents": {"gengu": 20, "wuxing": 18},
                    "attributes": {"strength": 15, "constitution": 12},
                },
            )
            
            def calc_status():
                _ = character.get_max_hp()
                _ = character.get_max_mp()
                _ = character.get_attack()
                _ = character.get_defense()
            
            result = benchmark(
                "角色状态计算",
                calc_status,
                iterations=1000,
                warmup=100,
            )
            
            print(f"\n{result}")
            # 断言：状态计算应小于1ms
            assert result.avg_time < 0.001
            
            await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_character_exp_gain(self):
        """测试角色经验获取性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            character = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key="perf_exp",
                attributes={"level": 1, "exp": 0},
            )
            
            def gain_exp():
                character.add_exp(10)
            
            result = benchmark(
                "角色经验获取",
                gain_exp,
                iterations=100,
                warmup=10,
            )
            
            print(f"\n{result}")
            # 断言：经验获取应小于0.1ms
            assert result.avg_time < 0.0001
            
            await engine.stop()


class TestEquipmentPerformance:
    """装备操作性能测试."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_equip_unequip_performance(self):
        """测试装备/卸下性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            character = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key="perf_equip",
                attributes={"level": 10},
            )
            
            sword = await engine.objects.create(
                typeclass_path="src.game.typeclasses.equipment.Equipment",
                key="perf_sword",
                location=character,
                attributes={"slot": EquipmentSlot.MAIN_HAND.value},
            )
            
            async def equip_unequip_cycle():
                await character.equip(sword)
                await character.unequip(EquipmentSlot.MAIN_HAND)
            
            result = await async_benchmark(
                "装备/卸下周期",
                equip_unequip_cycle,
                iterations=20,
                warmup=3,
            )
            
            print(f"\n{result}")
            # 断言：装备周期应小于20ms
            assert result.avg_time < 0.02
            
            await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_get_total_stats_performance(self):
        """测试装备属性计算性能（带缓存）."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            character = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key="perf_stats",
                attributes={"level": 10},
            )
            
            # 装备多个物品
            for i, slot in enumerate([EquipmentSlot.MAIN_HAND, EquipmentSlot.BODY, EquipmentSlot.HEAD]):
                item = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.equipment.Equipment",
                    key=f"perf_item_{i}",
                    location=character,
                    attributes={
                        "slot": slot.value,
                        "stats_bonus": {"attack": 10, "defense": 5},
                    },
                )
                await character.equip(item)
            
            def get_stats():
                _ = character.get_total_stats()
            
            result = benchmark(
                "装备属性计算（缓存）",
                get_stats,
                iterations=1000,
                warmup=100,
            )
            
            print(f"\n{result}")
            # 断言：带缓存的属性计算应小于0.01ms
            assert result.avg_time < 0.00001
            
            await engine.stop()


class TestRoomPerformance:
    """房间操作性能测试."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_room_desc_generation(self):
        """测试房间描述生成性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            room = await engine.objects.create(
                typeclass_path="src.game.typeclasses.room.Room",
                key="perf_room",
                attributes={
                    "description": "这是一个测试房间，用于性能测试。",
                    "coords": (0, 0, 0),
                },
            )
            
            def generate_desc():
                _ = room.at_desc(None)
            
            result = benchmark(
                "房间描述生成",
                generate_desc,
                iterations=1000,
                warmup=100,
            )
            
            print(f"\n{result}")
            # 断言：描述生成应小于0.1ms
            assert result.avg_time < 0.0001
            
            await engine.stop()


class TestDatabasePerformance:
    """数据库操作性能测试."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_batch_save_performance(self):
        """测试批量保存性能."""
        config = Config()
        with tempfile.TemporaryDirectory() as tmp:
            config.database.url = f"sqlite+aiosqlite:///{tmp}/test.db"
            
            engine = GameEngine(config)
            await engine.initialize()
            
            # 创建多个脏数据对象
            objects = []
            for i in range(20):
                obj = await engine.objects.create(
                    typeclass_path="src.engine.core.typeclass.TypeclassBase",
                    key=f"batch_save_{i}",
                )
                obj.key = f"modified_{i}"
                objects.append(obj)
            
            result = await async_benchmark(
                "批量保存20个对象",
                lambda: engine.objects.save_all(),
                iterations=10,
                warmup=2,
            )
            
            print(f"\n{result}")
            # 断言：批量保存应小于100ms
            assert result.avg_time < 0.1
            
            await engine.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark"])

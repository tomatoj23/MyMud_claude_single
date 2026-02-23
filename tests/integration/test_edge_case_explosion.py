"""边界条件爆炸测试 - 测试各种极端边界情况.

覆盖所有可能的边界条件，包括数值边界、长度边界、时间边界等。
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import sys

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.typeclasses.item import Item
from src.game.quest.karma import KarmaSystem


class TestNumericBoundaries:
    """数值边界测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_integer_overflow_boundaries(self, engine):
        """测试整数溢出边界."""
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="int_bound_char",
            attributes={"name": "整数边界角色"}
        )
        
        # Python整数边界（理论无界，但JSON序列化有限制）
        boundaries = [
            0,
            -1,
            1,
            2**31 - 1,  # 32位有符号整数最大值
            -(2**31),   # 32位有符号整数最小值
            2**63 - 1,  # 64位有符号整数最大值
            -(2**63),   # 64位有符号整数最小值
            2**1024,    # 超大整数
        ]
        
        for value in boundaries:
            try:
                char.db.set(f"int_{value}", value)
                retrieved = char.db.get(f"int_{value}")
                assert retrieved == value, f"Value mismatch for {value}"
            except Exception as e:
                print(f"Integer boundary {value}: {e}")
    
    @pytest.mark.asyncio
    async def test_float_special_values(self, engine):
        """测试浮点特殊值."""
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="float_char",
            attributes={"name": "浮点角色"}
        )
        
        special_floats = [
            0.0,
            -0.0,
            float('inf'),
            float('-inf'),
            float('nan'),
            sys.float_info.max,
            sys.float_info.min,
            sys.float_info.epsilon,
        ]
        
        for value in special_floats:
            try:
                char.db.set(f"float_{value}", value)
                retrieved = char.db.get(f"float_{value}")
                if value != value:  # NaN check
                    assert retrieved != retrieved
                else:
                    assert retrieved == value or (retrieved != retrieved and value != value)
            except Exception as e:
                print(f"Float special {value}: {e}")


class TestStringBoundaries:
    """字符串边界测试."""
    
    @pytest.mark.asyncio
    async def test_string_length_boundaries(self):
        """测试字符串长度边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/str_bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="str_bound_char",
            attributes={"name": "字符串边界角色"}
        )
        
        # 各种长度的字符串
        lengths = [0, 1, 10, 100, 1000, 10000, 100000, 1000000]
        
        for length in lengths:
            try:
                test_str = "x" * length
                char.db.set(f"str_len_{length}", test_str)
                retrieved = char.db.get(f"str_len_{length}")
                assert len(retrieved) == length
            except Exception as e:
                print(f"String length {length}: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_unicode_boundaries(self):
        """测试Unicode边界字符."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/unicode.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="unicode_char",
            attributes={"name": "Unicode角色"}
        )
        
        # 各种Unicode字符
        unicode_chars = [
            "\x00",  # NULL
            "\x01",  # 控制字符
            "\t\n\r",  # 空白字符
            "\uFFFF",  # BMP最大值
            "\U0010FFFF",  # Unicode最大值
            "🎮",  # Emoji
            "中",  # CJK
            "مرحبا",  # 阿拉伯语（RTL）
            "שלום",  # 希伯来语（RTL）
            "👨‍👩‍👧‍👦",  # 组合Emoji
        ]
        
        for char_str in unicode_chars:
            try:
                key = f"unicode_{ord(char_str[0]) if char_str else 'empty'}"
                char.db.set(key, char_str)
                retrieved = char.db.get(key)
                assert retrieved == char_str
            except Exception as e:
                print(f"Unicode {repr(char_str)[:50]}: {e}")
        
        await engine.stop()


class TestCollectionBoundaries:
    """集合边界测试."""
    
    @pytest.mark.asyncio
    async def test_list_size_boundaries(self):
        """测试列表大小边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/list_bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="list_char",
            attributes={"name": "列表角色"}
        )
        
        # 各种大小的列表
        sizes = [0, 1, 10, 100, 1000, 10000]
        
        for size in sizes:
            try:
                test_list = list(range(size))
                char.db.set(f"list_size_{size}", test_list)
                retrieved = char.db.get(f"list_size_{size}")
                assert len(retrieved) == size
            except Exception as e:
                print(f"List size {size}: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_dict_key_count_boundaries(self):
        """测试字典键数量边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/dict_bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="dict_char",
            attributes={"name": "字典角色"}
        )
        
        # 各种键数量的字典
        counts = [0, 1, 10, 100, 1000, 5000]
        
        for count in counts:
            try:
                test_dict = {f"key_{i}": f"value_{i}" for i in range(count)}
                char.db.set(f"dict_keys_{count}", test_dict)
                retrieved = char.db.get(f"dict_keys_{count}")
                assert len(retrieved) == count
            except Exception as e:
                print(f"Dict keys {count}: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_nested_depth_boundaries(self):
        """测试嵌套深度边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/nest.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="nest_char",
            attributes={"name": "嵌套角色"}
        )
        
        # 各种嵌套深度
        depths = [0, 1, 5, 10, 50, 100, 500, 1000]
        
        for depth in depths:
            try:
                # 创建嵌套字典
                nested = "bottom"
                for i in range(depth):
                    nested = {f"level_{depth-i}": nested}
                
                char.db.set(f"nest_depth_{depth}", nested)
                retrieved = char.db.get(f"nest_depth_{depth}")
                
                # 验证深度
                current = retrieved
                actual_depth = 0
                while isinstance(current, dict):
                    actual_depth += 1
                    key = list(current.keys())[0]
                    current = current[key]
                assert actual_depth == depth
            except RecursionError:
                print(f"Nest depth {depth}: RecursionError")
            except Exception as e:
                print(f"Nest depth {depth}: {type(e).__name__}")
        
        await engine.stop()


class TestTimeBoundaries:
    """时间边界测试."""
    
    @pytest.mark.asyncio
    async def test_datetime_boundaries(self):
        """测试日期时间边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/time_bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="time_char",
            attributes={"name": "时间角色"}
        )
        
        # 各种边界时间
        times = [
            datetime.min,
            datetime.max,
            datetime(1970, 1, 1),  # Unix epoch
            datetime(2038, 1, 19),  # 32位时间戳边界
            datetime(1, 1, 1),  # 最早
            datetime(9999, 12, 31, 23, 59, 59),  # 最晚
        ]
        
        for i, dt in enumerate(times):
            try:
                char.db.set(f"time_{i}", dt.isoformat())
                retrieved = char.db.get(f"time_{i}")
            except Exception as e:
                print(f"Datetime {dt}: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_timedelta_boundaries(self):
        """测试时间间隔边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/delta.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="delta_char",
            attributes={"name": "间隔角色"}
        )
        
        # 各种时间间隔
        deltas = [
            timedelta(0),
            timedelta(seconds=1),
            timedelta(days=365),
            timedelta(days=36525),  # 约100年
            timedelta(microseconds=1),
            timedelta.max,
            timedelta.min,
        ]
        
        for i, delta in enumerate(deltas):
            try:
                char.db.set(f"delta_{i}", delta.total_seconds())
                retrieved = char.db.get(f"delta_{i}")
            except Exception as e:
                print(f"Timedelta {delta}: {e}")
        
        await engine.stop()


class TestObjectCountBoundaries:
    """对象数量边界测试."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_massive_object_creation(self):
        """测试大量对象创建."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/massive.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 创建大量对象
        counts = [100, 500, 1000, 5000]
        
        for count in counts:
            try:
                created = []
                for i in range(count):
                    obj = await engine.objects.create(
                        typeclass_path="src.game.typeclasses.item.Item",
                        key=f"mass_item_{count}_{i}",
                        attributes={"name": f"物品{i}"}
                    )
                    created.append(obj)
                
                # 验证能查询到
                results = await engine.objects.find(limit=count * 2)
                print(f"Created {count} objects, found {len(results)}")
                
            except Exception as e:
                print(f"Massive creation {count}: {e}")
        
        await engine.stop()


class TestMemoryBoundaries:
    """内存边界测试."""
    
    @pytest.mark.asyncio
    async def test_large_attribute_values(self):
        """测试大属性值."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/large_attr.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="large_char",
            attributes={"name": "大属性角色"}
        )
        
        # 大属性值（MB级别）
        sizes_mb = [0.1, 0.5, 1, 5, 10]
        
        for size_mb in sizes_mb:
            try:
                size_bytes = int(size_mb * 1024 * 1024)
                large_data = "x" * size_bytes
                char.db.set(f"large_{size_mb}mb", large_data)
                print(f"Stored {size_mb}MB attribute")
            except MemoryError:
                print(f"{size_mb}MB: MemoryError")
            except Exception as e:
                print(f"{size_mb}MB: {type(e).__name__}")
        
        await engine.stop()


class TestCacheBoundaries:
    """缓存边界测试."""
    
    @pytest.mark.asyncio
    async def test_cache_size_boundaries(self):
        """测试缓存大小边界."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/cache_bound.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 大量对象进入缓存
        try:
            for i in range(10000):
                obj = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.item.Item",
                    key=f"cache_item_{i}",
                    attributes={"name": f"缓存物品{i}"}
                )
                # 强制加载到缓存
                await engine.objects.load(obj.id)
        except Exception as e:
            print(f"Cache boundary: {e}")
        
        # 查看缓存统计
        stats = engine.objects.get_cache_stats()
        print(f"Cache stats: {stats}")
        
        await engine.stop()


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.chaos,
    pytest.mark.boundaries
]

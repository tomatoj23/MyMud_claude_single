"""API混沌测试 - 以非常规方式调用API，测试鲁棒性.

测试各种API调用的边界情况、异常参数、非法状态。
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import inspect

from src.utils.config import Config
from src.engine.core import GameEngine
from src.engine.objects.manager import ObjectManager
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.typeclasses.item import Item


class TestAPICallVariations:
    """API调用变体测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/api_chaos.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_object_manager_with_none_params(self, engine):
        """测试ObjectManager传入None参数."""
        # 测试各种None参数情况
        try:
            await engine.objects.load(None)
        except (TypeError, ValueError, AttributeError) as e:
            print(f"load(None): {type(e).__name__}")
        
        try:
            await engine.objects.delete(None)
        except (TypeError, ValueError, AttributeError) as e:
            print(f"delete(None): {type(e).__name__}")
        
        try:
            await engine.objects.save(None)
        except (TypeError, ValueError, AttributeError) as e:
            print(f"save(None): {type(e).__name__}")
        
        try:
            engine.objects.mark_dirty(None)
        except (TypeError, ValueError, AttributeError) as e:
            print(f"mark_dirty(None): {type(e).__name__}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_object_manager_with_invalid_ids(self, engine):
        """测试ObjectManager传入无效ID."""
        # 数值型无效ID（这些应该能快速处理）
        invalid_ids = [
            -1,
            -999999,
            0,
            float('inf'),
            float('-inf'),
            float('nan'),
            "string_id",
        ]
        
        for invalid_id in invalid_ids:
            try:
                # 添加超时保护
                result = await asyncio.wait_for(
                    engine.objects.load(invalid_id),
                    timeout=5.0
                )
                # 应该返回None或抛出异常
            except asyncio.TimeoutError:
                print(f"load({type(invalid_id).__name__}): Timeout")
            except Exception as e:
                print(f"load({type(invalid_id).__name__}): {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_create_with_invalid_typeclass(self, engine):
        """测试使用无效typeclass创建对象."""
        invalid_typeclasses = [
            "",
            "not.a.real.Typeclass",
            "src.game.typeclasses.character.NonExistent",
            "<script>alert(1)</script>",
            "../../../etc/passwd",
            "a" * 10000,  # 超长字符串
            None,
            12345,
        ]
        
        for tc in invalid_typeclasses:
            try:
                obj = await engine.objects.create(
                    typeclass_path=tc,
                    key="test_key",
                    attributes={}
                )
            except Exception as e:
                print(f"create({str(tc)[:50]}): {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_create_with_malformed_attributes(self, engine):
        """测试使用畸形属性创建对象."""
        malformed_attrs = [
            None,
            "string_instead_of_dict",
            12345,
            [],
            {"__class__": None},  # 尝试覆盖特殊属性
            {"__dict__": {}},
            {"key" + "_" * 10000: "value"},  # 超长键名
            {"key": "v" * 10000000},  # 超大值
            {f"key_{i}": i for i in range(10000)},  # 超多键
        ]
        
        for attrs in malformed_attrs:
            try:
                obj = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.character.Character",
                    key="attr_test",
                    attributes=attrs if isinstance(attrs, dict) else {}
                )
            except Exception as e:
                print(f"create with {type(attrs).__name__}: {type(e).__name__}")


class TestAttributeAccessChaos:
    """属性访问混沌测试."""
    
    @pytest.mark.asyncio
    async def test_db_operations_edge_cases(self):
        """测试db操作边界情况."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/db_chaos.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="db_chaos_char",
            attributes={"name": "DB混沌角色"}
        )
        
        # 测试各种边界键名
        edge_keys = [
            "",
            "   ",
            "__init__",
            "__class__",
            "__dict__",
            "__module__",
            "_private",
            "123numeric",
            "key with spaces",
            "key\nwith\nnewlines",
            "key\twith\ttabs",
            "🔥emoji🔥key🔥",
            "a" * 10000,
        ]
        
        for key in edge_keys:
            try:
                char.db.set(key, "test_value")
                value = char.db.get(key)
            except Exception as e:
                print(f"db['{key[:50]}...']: {type(e).__name__}")
        
        # 测试各种边界值
        edge_values = [
            None,
            "",
            [],
            {},
            set(),  # 不可序列化
            lambda x: x,  # 函数
            char,  # 循环引用
            float('inf'),
            float('-inf'),
            float('nan'),
        ]
        
        for value in edge_values:
            try:
                char.db.set(f"key_{type(value).__name__}", value)
            except Exception as e:
                print(f"db set {type(value).__name__}: {type(e).__name__}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_property_access_after_deletion(self):
        """测试删除后访问属性."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/prop_del.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="del_char",
            attributes={"name": "删除测试角色", "hp": 100}
        )
        
        char_id = char.id
        
        # 删除对象
        await engine.objects.delete(char)
        
        # 尝试访问已删除对象的属性
        try:
            hp = char.hp
        except Exception as e:
            print(f"Access after delete: {type(e).__name__}")
        
        try:
            char.db.set("hp", 50)
        except Exception as e:
            print(f"Set after delete: {type(e).__name__}")
        
        await engine.stop()


class TestMethodCallChaos:
    """方法调用混沌测试."""
    
    @pytest.mark.asyncio
    async def test_equip_calls_with_chaos(self):
        """测试装备方法的混沌调用."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/equip_chaos.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="equip_chaos_char",
            attributes={"name": "装备混沌角色"}
        )
        
        # 创建各种奇怪的装备对象
        chaos_equips = [
            None,
            char,  # 装备自己
            MagicMock(),  # Mock对象
            "string",
            12345,
            [],
            {},
        ]
        
        for equip in chaos_equips:
            try:
                await char.equipment_equip(equip)
            except Exception as e:
                print(f"equip({type(equip).__name__}): {type(e).__name__}")
        
        # 测试多次装备同一件装备
        sword = await engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="chaos_sword",
            attributes={"name": "混沌剑"}
        )
        sword.location = char
        
        for _ in range(10):
            try:
                await char.equipment_equip(sword)
            except Exception as e:
                print(f"Repeated equip: {type(e).__name__}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_find_with_chaos_params(self):
        """测试find方法混沌参数."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/find_chaos.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 创建测试数据
        for i in range(10):
            await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"find_test_{i}",
                attributes={"name": f"查找测试{i}"}
            )
        
        # 混沌查询参数
        chaos_params = [
            {"typeclass_path": None},
            {"typeclass_path": ""},
            {"typeclass_path": "Invalid.Path"},
            {"location": None},
            {"location": "string"},
            {"key_contains": None},
            {"key_contains": ""},
            {"key_contains": "a" * 10000},
            {"limit": -1},
            {"limit": 0},
            {"limit": 999999},
            {"limit": float('inf')},
            {"use_cache": None},
            {"invalid_param": "value"},  # 无效参数
        ]
        
        for params in chaos_params:
            try:
                results = await engine.objects.find(**params)
            except Exception as e:
                print(f"find({params}): {type(e).__name__}")
        
        await engine.stop()


class TestStateTransitionChaos:
    """状态转换混沌测试."""
    
    @pytest.mark.asyncio
    async def test_rapid_state_transitions(self):
        """测试快速状态转换."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/state_trans.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        # 快速启动停止
        for i in range(10):
            try:
                await engine.stop()
            except:
                pass
            try:
                await engine.start()
            except:
                pass
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_save_during_operations(self):
        """测试操作进行中保存."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/save_during.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="save_during_char",
            attributes={"name": "保存中断角色"}
        )
        
        # 修改属性同时保存
        async def modify_attrs():
            for i in range(100):
                char.db.set(f"attr_{i}", i)
        
        async def save_repeatedly():
            for _ in range(20):
                await engine.objects.save(char)
        
        # 并发执行
        await asyncio.gather(
            modify_attrs(),
            save_repeatedly(),
            return_exceptions=True
        )
        
        await engine.stop()


class TestReflectionAndIntrospection:
    """反射和内省混沌测试."""
    
    @pytest.mark.asyncio
    async def test_modify_internal_state(self):
        """测试修改内部状态."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/reflect.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="reflect_char",
            attributes={"name": "反射角色"}
        )
        
        # 尝试修改内部属性
        try:
            char._id = -1  # 修改ID
        except:
            pass
        
        try:
            char.__dict__['_data'] = None
        except:
            pass
        
        try:
            # 尝试添加特殊方法
            char.__len__ = lambda self: 0
        except:
            pass
        
        # 验证对象仍然可用
        try:
            _ = char.id
        except Exception as e:
            print(f"After internal modify: {type(e).__name__}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_call_private_methods(self):
        """测试调用私有方法."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/private.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 尝试调用ObjectManager的私有方法
        try:
            engine.objects._ObjectManager__l1_cache = {}
        except:
            pass
        
        try:
            engine.objects._invalidate_query_cache()
        except Exception as e:
            print(f"Call private method: {type(e).__name__}")
        
        await engine.stop()


class TestNumericEdgeCases:
    """数值边界情况测试."""
    
    @pytest.mark.asyncio
    async def test_extreme_numeric_values(self):
        """测试极端数值."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/numeric.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="numeric_char",
            attributes={"name": "数值角色"}
        )
        
        # 极端数值
        extreme_values = {
            "hp": float('inf'),
            "max_hp": float('-inf'),
            "level": float('nan'),
            "exp": 1e308,  # 接近最大浮点数
            "gold": -1e308,
            "strength": 2**1024,  # 超大整数
        }
        
        for key, value in extreme_values.items():
            try:
                char.db.set(key, value)
                retrieved = char.db.get(key)
            except Exception as e:
                print(f"Set {key}={value}: {type(e).__name__}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_decimal_precision_issues(self):
        """测试小数精度问题."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/decimal.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="decimal_char",
            attributes={"name": "小数角色"}
        )
        
        # 浮点数精度问题
        problematic_values = [
            0.1 + 0.2,  # 不等于0.3
            1 / 3,
            float('1e-1000'),  # 下溢
            1e309,  # 上溢
        ]
        
        for value in problematic_values:
            try:
                char.db.set("float_test", value)
            except Exception as e:
                print(f"Set {value}: {type(e).__name__}")
        
        await engine.stop()


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.chaos,
    pytest.mark.api_chaos
]

"""混沌玩家行为测试 - 模拟非理性、无逻辑、随机、不可预知的单机玩家行为.

测试各种异常操作序列、状态污染、时序混乱等场景，发现潜在问题。
"""
import pytest
import asyncio
import tempfile
import random
import string
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot, EquipmentQuality
from src.game.typeclasses.item import Item
from src.game.npc.core import NPC, NPCType
from src.game.quest.core import Quest, QuestObjective, QuestObjectiveType, QuestType
from src.game.quest.karma import KarmaSystem
from src.game.combat.core import CombatSession, CombatAction, CombatResult


class TestRandomCommandSequences:
    """随机命令序列测试 - 玩家乱点乱按."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/chaos.db"
        config.game.auto_save_interval = 60
        
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_random_command_inputs(self, engine):
        """测试随机命令输入."""
        random_commands = [
            "",  # 空命令
            "   ",  # 只有空格
            "!@#$%^&*()",  # 特殊字符
            "look look look",  # 重复命令
            "go nowhere",  # 无效方向
            "kill",  # 缺少目标
            "kill myself",  # 自杀尝试
            "use",  # 缺少物品
            "use nonexistent_item",  # 不存在的物品
            "talk",  # 缺少NPC
            "inventory 12345",  # 多余参数
            "equip sword shield helmet",  # 过多参数
            "drop all",  # 批量丢弃
            "give",  # 缺少目标和物品
            "cast",  # 缺少技能
            "cast fireball at tree",  # 无效目标
            "\\\\\\",  # 转义字符
            "\n\t\r",  # 控制字符
            "a" * 1000,  # 超长命令
            "中文命令测试",  # 非英文命令
        ]
        
        for cmd in random_commands:
            try:
                # 随机命令不应该导致崩溃
                result = await engine.process_input(cmd)
                # 可以接受成功或失败，但不能抛出未处理异常
            except Exception as e:
                # 记录但不失败 - 我们需要知道有什么异常
                print(f"Command '{cmd[:50]}...' raised: {type(e).__name__}: {e}")
    
    @pytest.mark.asyncio
    async def test_rapid_random_commands(self, engine):
        """测试快速随机命令轰炸."""
        commands_pool = [
            "look", "inventory", "status", "help",
            "go north", "go south", "go east", "go west",
            "attack", "defend", "flee",
            "", "xyz", "123", "!!!",
        ]
        
        # 快速执行50个随机命令
        for _ in range(50):
            cmd = random.choice(commands_pool)
            try:
                await engine.process_input(cmd)
            except Exception as e:
                # 不应因快速输入而崩溃
                print(f"Rapid command failed: {e}")
    
    @pytest.mark.asyncio
    async def test_command_injection_attempts(self, engine):
        """测试命令注入尝试."""
        injection_commands = [
            "look; drop all",  # 命令分隔符
            "look && drop all",  # 逻辑运算符
            "look | cat /etc/passwd",  # 管道符
            "look `rm -rf /`",  # 反引号
            "look $(whoami)",  # 命令替换
            "look <!-- script -->",  # HTML注释
            "look <!--#exec cmd=\"ls\"-->",  # SSI注入
        ]
        
        for cmd in injection_commands:
            try:
                await engine.process_input(cmd)
            except Exception as e:
                print(f"Injection attempt raised: {e}")


class TestIllogicalOperationSequences:
    """非逻辑操作序列测试 - 不按正常流程使用功能."""
    
    @pytest.mark.asyncio
    async def test_equip_before_obtain(self):
        """测试获得物品前就尝试装备."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/sequence.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="sequence_char",
            attributes={"name": "序列测试角色"}
        )
        
        # 创建一个不属于玩家的装备
        sword = await engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="sequence_sword",
            attributes={"name": "测试剑"}
        )
        sword.slot = EquipmentSlot.MAIN_HAND
        # sword.location 不是 char
        
        # 尝试装备不在背包里的物品（应该失败或处理得当）
        try:
            result = await char.equip(sword)
            # 根据实现，可能返回False或抛出异常
        except Exception as e:
            print(f"Equip before obtain: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_use_item_before_pickup(self):
        """测试拾取前就使用物品."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/use.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="use_char",
            attributes={"name": "使用测试角色"}
        )
        
        potion = await engine.objects.create(
            typeclass_path="src.game.typeclasses.item.Item",
            key="potion",
            attributes={"name": "药水", "can_use": True}
        )
        # 药水不在玩家背包里
        
        # 尝试使用不在背包里的物品
        try:
            await potion.on_use(char)
        except Exception as e:
            print(f"Use before pickup: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_talk_to_dead_npc(self):
        """测试与已死亡NPC对话."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/dead.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="dead_npc",
            attributes={"name": "死亡NPC", "hp": 0, "is_alive": False}
        )
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="talker",
            attributes={"name": "对话者"}
        )
        
        # 尝试与死亡NPC交互
        try:
            # 模拟对话
            if hasattr(npc, 'talk'):
                await npc.talk(char)
        except Exception as e:
            print(f"Talk to dead NPC: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_complete_quest_without_accepting(self):
        """测试未接受任务就尝试完成."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/quest.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="quest_char",
            attributes={"name": "任务测试角色"}
        )
        
        # 尝试更新未接受任务的进度
        try:
            # 假设有任务系统接口
            if hasattr(char, 'update_quest_progress'):
                await char.update_quest_progress("unaccepted_quest", 1)
        except Exception as e:
            print(f"Complete without accept: {e}")
        
        await engine.stop()


class TestStatePollution:
    """状态污染测试 - 在错误状态下尝试操作."""
    
    @pytest.mark.asyncio
    async def test_actions_while_dead(self):
        """测试死亡状态下执行各种操作."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/dead_state.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="dead_char",
            attributes={"name": "死亡角色", "hp": 0}
        )
        
        # 死亡状态下尝试各种操作
        dead_actions = [
            lambda: char.equip(None) if hasattr(char, 'equip') else None,
            lambda: char.unequip(EquipmentSlot.MAIN_HAND) if hasattr(char, 'unequip') else None,
            lambda: char.move("north") if hasattr(char, 'move') else None,
            lambda: char.attack(None) if hasattr(char, 'attack') else None,
            lambda: char.use_item(None) if hasattr(char, 'use_item') else None,
        ]
        
        for action in dead_actions:
            try:
                result = action()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Dead state action: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_equip_while_in_combat(self):
        """测试战斗中更换装备."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/combat_equip.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="combat_char",
            attributes={"name": "战斗角色"}
        )
        char.db = MagicMock()
        char.db.get = MagicMock(return_value={})
        char.db.set = MagicMock()
        
        sword = await engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="combat_sword",
            attributes={"name": "战斗剑"}
        )
        sword.location = char
        
        # 标记为战斗中（如果系统支持）
        try:
            if hasattr(char, 'in_combat'):
                char.in_combat = True
                await char.equip(sword)
        except Exception as e:
            print(f"Equip while in combat: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_move_while_stunned(self):
        """测试眩晕状态下移动."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/stun.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="stun_char",
            attributes={"name": "眩晕角色"}
        )
        
        # 添加眩晕状态
        try:
            if hasattr(char, 'add_status'):
                await char.add_status("stunned", duration=5)
            
            # 尝试移动
            if hasattr(char, 'move'):
                await char.move("north")
        except Exception as e:
            print(f"Move while stunned: {e}")
        
        await engine.stop()


class TestTimingChaos:
    """时序混乱测试 - 操作顺序完全随机."""
    
    @pytest.mark.asyncio
    async def test_random_save_load_timing(self):
        """测试随机保存/加载时机."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/timing.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="timing_char",
            attributes={"name": "时序角色", "hp": 100}
        )
        
        # 随机操作序列
        operations = [
            lambda: engine.objects.mark_dirty(char),
            lambda: engine.objects.save(char),
            lambda: engine.objects.save_all(),
            lambda: engine.objects.load(char.id),
            lambda: setattr(char.attributes, 'hp', random.randint(1, 100)),
        ]
        
        # 随机执行20个操作
        for _ in range(20):
            op = random.choice(operations)
            try:
                result = op()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Random timing op: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_interrupt_mid_operation(self):
        """测试操作中途中断."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/interrupt.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="interrupt_char",
            attributes={"name": "中断角色"}
        )
        
        # 模拟操作中途引擎停止
        async def long_operation():
            char.attributes = {"hp": 50}
            await asyncio.sleep(0.1)
            char.attributes = {"hp": 100}
        
        task = asyncio.create_task(long_operation())
        await asyncio.sleep(0.05)  # 操作中途
        
        # 强制停止引擎
        await engine.stop()
        
        try:
            await task
        except asyncio.CancelledError:
            print("Operation cancelled as expected")
        except Exception as e:
            print(f"Interrupt exception: {e}")


class TestDataPollution:
    """数据污染测试 - 使用异常数据调用API."""
    
    @pytest.mark.asyncio
    async def test_api_with_corrupted_data(self):
        """测试使用损坏数据调用API."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/corrupt.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="corrupt_char",
            attributes={"name": "损坏数据角色"}
        )
        
        # 使用损坏的数据调用各种方法
        corrupted_data_tests = [
            # 损坏的属性类型
            lambda: setattr(char.db, '_data', None) if hasattr(char, 'db') else None,
            lambda: setattr(char.db, '_data', "string_instead_of_dict") if hasattr(char, 'db') else None,
            lambda: setattr(char.db, '_data', []) if hasattr(char, 'db') else None,
            # 损坏的数值
            lambda: char.db.set("hp", "not_a_number") if hasattr(char.db, 'set') else None,
            lambda: char.db.set("level", -999) if hasattr(char.db, 'set') else None,
            lambda: char.db.set("name", None) if hasattr(char.db, 'set') else None,
        ]
        
        for test in corrupted_data_tests:
            try:
                result = test()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Corrupted data test: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_type_confusion_attacks(self):
        """测试类型混淆攻击."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/type.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="type_char",
            attributes={"name": "类型测试角色"}
        )
        
        # 尝试用错误类型调用方法
        type_confusion_tests = [
            lambda: char.equip("string_instead_of_equipment") if hasattr(char, 'equip') else None,
            lambda: char.equip(12345) if hasattr(char, 'equip') else None,
            lambda: char.equip(None) if hasattr(char, 'equip') else None,
            lambda: char.equip(char) if hasattr(char, 'equip') else None,  # 自己装备自己
            lambda: char.move(123) if hasattr(char, 'move') else None,  # 数字作为方向
            lambda: char.move(None) if hasattr(char, 'move') else None,
        ]
        
        for test in type_confusion_tests:
            try:
                result = test()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Type confusion: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_circular_reference_creation(self):
        """测试循环引用创建."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/circular.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="circular_char",
            attributes={"name": "循环引用角色"}
        )
        
        # 创建循环引用
        try:
            char.db.set("self_reference", char) if hasattr(char.db, 'set') else None
            char.db.set("circular_dict", {"a": {"b": {"a_ref": None}}})
            
            # 获取数据看是否能正确处理
            data = char.db.get("circular_dict")
        except Exception as e:
            print(f"Circular reference: {e}")
        
        await engine.stop()


class TestExtremeCombinations:
    """极端组合测试 - 多种异常条件同时出现."""
    
    @pytest.mark.asyncio
    async def test_multiple_extreme_conditions(self):
        """测试多种极端条件同时出现."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/extreme.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 创建一个处于多重极端状态的角色
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="extreme_char",
            attributes={
                "name": "",  # 空名字
                "hp": 0,  # 零生命
                "level": 0,  # 零等级（可能无效）
                "exp": -1000,  # 负经验
                "gold": -999999,  # 负金币
                "strength": 999999,  # 超高压属性
                "inventory": None,  # 空背包
            }
        )
        
        # 在这种状态下尝试各种操作
        extreme_actions = [
            lambda: char.db.get("nonexistent_key"),
            lambda: char.db.set("hp", float('inf')),
            lambda: char.db.set("level", float('nan')),
            lambda: engine.objects.mark_dirty(char),
            lambda: engine.objects.save(char),
        ]
        
        for action in extreme_actions:
            try:
                result = action()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Extreme condition: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_simultaneous_status_effects(self):
        """测试同时施加大量状态效果."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/status.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="status_char",
            attributes={"name": "状态角色"}
        )
        
        # 尝试同时添加大量状态（如果支持）
        if hasattr(char, 'add_status'):
            for i in range(100):  # 100个状态
                try:
                    await char.add_status(f"status_{i}", duration=random.randint(-10, 1000))
                except Exception as e:
                    print(f"Status {i}: {e}")
        
        await engine.stop()


class TestInfiniteLoopsAndRecursion:
    """无限循环/递归测试 - 检查栈溢出."""
    
    @pytest.mark.asyncio
    async def test_deep_recursion_in_attributes(self):
        """测试属性中的深度递归."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/recursion.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="recursion_char",
            attributes={"name": "递归角色"}
        )
        
        # 创建深嵌套结构（但不至于崩溃）
        depth = 500
        nested = {}
        current = nested
        for i in range(depth):
            current['child'] = {}
            current = current['child']
        current['value'] = "bottom"
        
        try:
            char.db.set("deep_nested", nested)
            retrieved = char.db.get("deep_nested")
        except RecursionError:
            print("RecursionError as expected for deep nesting")
        except Exception as e:
            print(f"Deep recursion: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio  
    async def test_self_referential_structures(self):
        """测试自引用结构."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/self_ref.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="self_ref_char",
            attributes={"name": "自引用角色"}
        )
        
        # 创建自引用结构
        a = {}
        b = {'ref': a}
        a['ref'] = b  # 循环引用
        
        try:
            char.db.set("circular", a)
            # 尝试序列化可能会导致问题
        except Exception as e:
            print(f"Self-referential: {e}")
        
        await engine.stop()


class TestResourceExhaustion:
    """资源耗尽测试 - 边界情况."""
    
    @pytest.mark.asyncio
    async def test_rapid_object_creation_deletion(self):
        """测试快速创建删除对象."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/exhaust.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        # 快速创建和删除
        for i in range(100):
            try:
                obj = await engine.objects.create(
                    typeclass_path="src.game.typeclasses.item.Item",
                    key=f"temp_item_{i}",
                    attributes={"name": f"临时物品{i}"}
                )
                await engine.objects.delete(obj.id)
            except Exception as e:
                print(f"Rapid create/delete {i}: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_massive_attribute_updates(self):
        """测试大量属性更新."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/massive.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="massive_char",
            attributes={"name": "大量更新角色"}
        )
        
        # 快速更新属性1000次
        for i in range(1000):
            try:
                char.db.set(f"attr_{i}", f"value_{i}")
                engine.objects.mark_dirty(char)
            except Exception as e:
                print(f"Attribute update {i}: {e}")
        
        # 尝试保存
        try:
            await engine.objects.save(char)
        except Exception as e:
            print(f"Save after massive updates: {e}")
        
        await engine.stop()


class TestCrazyPlayerBehavior:
    """疯狂玩家行为测试 - 完全不合理的游戏方式."""
    
    @pytest.mark.asyncio
    async def test_spam_same_command_1000_times(self):
        """测试重复发送同一命令1000次."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/spam.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        # 疯狂发送look命令
        for i in range(1000):
            try:
                await engine.process_input("look")
            except Exception as e:
                print(f"Spam command {i}: {e}")
                break
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_random_walk_simulation(self):
        """测试随机游走模拟."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/walk.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        await engine.start()
        
        directions = ["north", "south", "east", "west", "up", "down", "random", "invalid"]
        
        # 随机移动100次
        for _ in range(100):
            direction = random.choice(directions)
            try:
                await engine.process_input(f"go {direction}")
            except Exception as e:
                print(f"Random walk: {e}")
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_inventory_manipulation_chaos(self):
        """测试背包操作混乱."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/inv_chaos.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="inv_chaos_char",
            attributes={"name": "背包混乱角色"}
        )
        
        # 创建一些物品
        items = []
        for i in range(20):
            item = await engine.objects.create(
                typeclass_path="src.game.typeclasses.item.Item",
                key=f"chaos_item_{i}",
                attributes={"name": f"混乱物品{i}"}
            )
            item.location = char
            items.append(item)
        
        # 疯狂随机操作背包
        operations = ["equip", "unequip", "drop", "use", "examine", "give"]
        for _ in range(50):
            op = random.choice(operations)
            target = random.choice(items) if items else None
            try:
                if op == "equip" and target:
                    await char.equip(target)
                elif op == "unequip":
                    await char.unequip(EquipmentSlot.MAIN_HAND)
                # 其他操作...
            except Exception as e:
                print(f"Inventory chaos: {e}")
        
        await engine.stop()


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.chaos,
    pytest.mark.player_behavior
]

"""阶段二游戏系统集成测试.

测试武侠世界的完整游戏场景:
- 角色创建与成长
- 装备系统
- 武学系统
- 地图系统
- 跨系统交互
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from src.engine.core.engine import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentQuality, EquipmentSlot
from src.game.typeclasses.item import Item
from src.game.typeclasses.room import Exit, Room
from src.game.typeclasses.wuxue import (
    Kungfu,
    Move,
    WuxueType,
    get_counter_modifier,
)
from src.game.world.pathfinding import PathFinder
from src.utils.config import Config

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine


@pytest.fixture
async def game_engine(tmp_path: Path):
    """创建并初始化的游戏引擎."""
    config = Config()
    config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    config.game.auto_save_interval = 3600  # 禁用自动保存避免干扰

    engine = GameEngine(config)
    await engine.initialize()
    await engine.start()

    yield engine

    if engine.running:
        await engine.stop()


class TestCharacterCreationFlow:
    """角色创建完整流程测试."""

    @pytest.mark.asyncio
    async def test_create_character_with_talents(self, game_engine: GameEngine):
        """测试创建带先天资质的角色."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="令狐冲",
            attributes={
                "birth_talents": {"gengu": 25, "wuxing": 20, "fuyuan": 18, "rongmao": 22},
                "menpai": "华山派",
                "internal_type": "紫霞神功",
            },
        )

        assert isinstance(character, Character)
        assert character.birth_talents["gengu"] == 25
        assert character.birth_talents["wuxing"] == 20
        assert character.menpai == "华山派"
        assert character.internal_type == "紫霞神功"

    @pytest.mark.asyncio
    async def test_character_level_up_flow(self, game_engine: GameEngine):
        """测试角色升级流程."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="郭靖",
            attributes={
                "level": 1,
                "exp": 0,
                "birth_talents": {"gengu": 20, "wuxing": 15, "fuyuan": 20, "rongmao": 15},
            },
        )

        # 记录初始属性
        initial_level = character.level
        initial_max_hp = character.get_max_hp()

        # 添加经验升级 (2级需要 2*2*100=400 经验)
        leveled_up = character.add_exp(450)

        assert leveled_up is True
        assert character.level == initial_level + 1
        assert character.exp == 450  # 经验累积，不会扣除
        # 当前实现升级不直接增加属性，属性由 birth_talents 和 attributes 计算
        # 升级后满血复活，所以状态会重置
        assert character.get_hp()[0] == character.get_max_hp()  # 满血

    @pytest.mark.asyncio
    async def test_character_death_and_revive(self, game_engine: GameEngine):
        """测试角色死亡和复活."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="杨过",
            attributes={
                "level": 10,
                "exp": 1000,
            },
        )

        # 设置满血
        character._recalculate_status()
        original_exp = character.exp

        # 死亡
        character.at_death()

        # 验证死亡惩罚
        assert character.exp < original_exp  # 损失10%经验
        assert character.get_hp()[0] == character.get_max_hp()  # 满血复活


class TestEquipmentSystemFlow:
    """装备系统完整流程测试."""

    @pytest.mark.asyncio
    async def test_equip_item_flow(self, game_engine: GameEngine):
        """测试装备穿戴完整流程."""
        # 创建角色
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="剑客",
            attributes={"level": 10, "menpai": "华山派", "attributes": {"strength": 20}},
        )

        # 创建装备
        sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="精铁长剑",
            location=character,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "quality": EquipmentQuality.UNCOMMON.value,
                "stats_bonus": {"attack": 20, "agility": 5},
                "level_requirement": 5,
            },
        )

        # 记录装备前攻击力
        base_attack = character.get_attack()

        # 装备武器
        success, msg = await character.equipment_equip(sword)
        assert success is True
        assert character.equipment_slots.get("main_hand") == sword.id

        # 验证装备加成通过 get_total_stats 计算
        total_stats = character.equipment_get_stats()
        assert total_stats.get("attack") == 20
        assert total_stats.get("agility") == 5

    @pytest.mark.asyncio
    async def test_equip_requirements_check(self, game_engine: GameEngine):
        """测试装备要求检查."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="新手",
            attributes={"level": 5, "menpai": "华山派"},
        )

        # 创建高等级装备
        legendary_sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="绝世好剑",
            location=character,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "quality": EquipmentQuality.LEGENDARY.value,
                "level_requirement": 50,
                "menpai_requirement": "华山派",
            },
        )

        # 尝试装备（等级不足）
        can_equip, reason = legendary_sword.can_equip_by(character)
        assert can_equip is False
        assert "等级" in reason

    @pytest.mark.asyncio
    async def test_equip_durability_and_unequip(self, game_engine: GameEngine):
        """测试装备耐久和卸下流程."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="战士",
            attributes={"level": 10},
        )

        armor = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="铁甲",
            location=character,
            attributes={
                "slot": EquipmentSlot.BODY.value,
                "durability": (100, 100),
                "stats_bonus": {"defense": 30},
            },
        )

        # 装备
        await character.equipment_equip(armor)

        # 验证属性加成
        total_stats = character.equipment_get_stats()
        assert total_stats.get("defense") == 30

        # 损坏装备
        armor.modify_durability(-150)  # 超过最大耐久损失
        assert armor.is_broken is True

        # 损坏装备不应提供属性加成
        total_stats = character.equipment_get_stats()
        assert total_stats.get("defense", 0) == 0

        # 卸下装备
        success, msg = await character.equipment_unequip(EquipmentSlot.BODY)
        assert success is True
        assert character.equipment_slots.get("body") is None

    @pytest.mark.asyncio
    async def test_equip_binding(self, game_engine: GameEngine):
        """测试装备绑定."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="绑定测试",
            attributes={"level": 10},
        )

        sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="绑定剑",
            location=character,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
            },
        )

        # 装备前未绑定
        assert sword.is_bound is False

        # 装备后绑定
        await character.equipment_equip(sword)
        assert sword.is_bound is True


class TestWuxueSystemFlow:
    """武学系统完整流程测试."""

    @pytest.mark.asyncio
    async def test_learn_kungfu_flow(self, game_engine: GameEngine):
        """测试学习武功流程."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="武学家",
            attributes={
                "menpai": "少林派",
                "level": 20,
                "birth_talents": {"wuxing": 25},
            },
        )

        # 创建武功
        kungfu = Kungfu(
            key="罗汉拳",
            name="罗汉拳",
            wuxue_type=WuxueType.QUAN,
            menpai="少林派",
            requirements={"level": 10, "wuxing": 15},
            moves=[
                Move(key="罗汉举鼎", name="罗汉举鼎", wuxue_type=WuxueType.QUAN, mp_cost=10),
                Move(key="金刚伏魔", name="金刚伏魔", wuxue_type=WuxueType.QUAN, mp_cost=20),
            ],
        )

        # 检查学习条件
        can_learn, reason = kungfu.can_learn(character)
        assert can_learn is True

        # 学习武功
        success, msg = await character.wuxue_learn(kungfu)
        assert success is True
        assert character.wuxue_has_learned("罗汉拳") is True
        assert character.wuxue_get_level("罗汉拳") == 1

    @pytest.mark.asyncio
    async def test_practice_and_level_up(self, game_engine: GameEngine):
        """测试练习和武功升级."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="练习者",
            attributes={"menpai": "武当派", "level": 15, "birth_talents": {"wuxing": 20}},
        )

        # 创建武功
        move = Move(key="野马分鬃", name="野马分鬃", wuxue_type=WuxueType.QUAN, mp_cost=10)
        kungfu = Kungfu(
            key="武当长拳",
            name="武当长拳",
            wuxue_type=WuxueType.QUAN,
            menpai="武当派",
            moves=[move],
        )

        # 学习武功
        await character.wuxue_learn(kungfu)

        initial_level = character.wuxue_get_level("武当长拳")

        # 练习招式直到升级
        for _ in range(110):  # 1级需要100熟练度
            await character.wuxue_practice(kungfu, move)

        assert character.wuxue_get_level("武当长拳") > initial_level

    @pytest.mark.asyncio
    async def test_counter_matrix(self, game_engine: GameEngine):
        """测试武学克制关系."""
        # 拳克掌/指
        modifier = get_counter_modifier(WuxueType.QUAN, WuxueType.ZHANG)
        assert modifier == 1.2  # 1 + 0.2

        # 掌克指/剑
        modifier = get_counter_modifier(WuxueType.ZHANG, WuxueType.ZHI)
        assert modifier == 1.2

        # 指克剑/刀
        modifier = get_counter_modifier(WuxueType.ZHI, WuxueType.JIAN)
        assert modifier == 1.2

        # 无克制关系
        modifier = get_counter_modifier(WuxueType.NEIGONG, WuxueType.QUAN)
        assert modifier == 1.0

        # 被克制（掌被拳克）
        modifier = get_counter_modifier(WuxueType.ZHANG, WuxueType.QUAN)
        assert modifier == 0.85  # 1 - 0.15


class TestMapSystemFlow:
    """地图系统完整流程测试."""

    @pytest.mark.asyncio
    async def test_create_rooms_and_exits(self, game_engine: GameEngine):
        """测试创建房间和出口."""
        # 创建房间
        room1 = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Room",
            key="扬州城广场",
            attributes={
                "coords": (0, 0, 0),
                "area": "扬州城",
                "description": "扬州城的中心广场，人来人往。",
            },
        )

        room2 = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Room",
            key="扬州城北门",
            attributes={
                "coords": (0, 1, 0),
                "area": "扬州城",
                "description": "扬州城的北城门。",
            },
        )

        # 创建出口 - 使用 destination 直接设置目标房间对象
        exit_north = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Exit",
            key="北门",
            location=room1,
            attributes={
                "direction": "n",
            },
        )
        exit_north.destination = room2  # 直接设置目的地

        exit_south = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Exit",
            key="南门",
            location=room2,
            attributes={
                "direction": "s",
            },
        )
        exit_south.destination = room1  # 直接设置目的地

        # 验证出口属性
        assert exit_north.direction == "n"
        assert exit_north.destination_id == room2.id
        assert exit_south.direction == "s"
        assert exit_south.destination_id == room1.id
        # 验证方向名称
        assert exit_north.direction_name == "北"
        assert exit_south.direction_name == "南"

    @pytest.mark.asyncio
    async def test_character_movement(self, game_engine: GameEngine):
        """测试角色移动."""
        # 创建两个房间
        room1 = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Room",
            key="房间1",
            attributes={"coords": (0, 0, 0)},
        )

        room2 = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Room",
            key="房间2",
            attributes={"coords": (0, 1, 0)},
        )

        # 创建出口
        await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.room.Exit",
            key="北门",
            location=room1,
            attributes={"direction": "n", "destination_id": room2.id},
        )

        # 创建角色并放置
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="旅行者",
            location=room1,
        )

        assert character.location.id == room1.id

        # 移动角色
        character.location = room2
        assert character.location.id == room2.id

    @pytest.mark.asyncio
    async def test_pathfinding(self, game_engine: GameEngine):
        """测试寻路系统 - 使用简化的 mock 对象."""
        from unittest.mock import MagicMock, PropertyMock

        # 创建简单的 3 房间链式结构用于测试
        rooms = []
        for i in range(3):
            room = MagicMock()
            room.id = 1000 + i
            room.coords = (i, 0, 0)
            room.key = f"测试房间_{i}"
            rooms.append(room)

        # 创建出口连接
        # 房间0 -> 房间1 (东)
        exit_01 = MagicMock()
        exit_01.direction = "e"
        exit_01.destination_id = rooms[1].id
        exit_01.destination = rooms[1]

        # 房间1 -> 房间0 (西)
        exit_10 = MagicMock()
        exit_10.direction = "w"
        exit_10.destination_id = rooms[0].id
        exit_10.destination = rooms[0]

        # 房间1 -> 房间2 (东)
        exit_12 = MagicMock()
        exit_12.direction = "e"
        exit_12.destination_id = rooms[2].id
        exit_12.destination = rooms[2]

        # 房间2 -> 房间1 (西)
        exit_21 = MagicMock()
        exit_21.direction = "w"
        exit_21.destination_id = rooms[1].id
        exit_21.destination = rooms[1]

        # 设置房间的出口
        rooms[0].get_exits = MagicMock(return_value=[exit_01])
        rooms[1].get_exits = MagicMock(return_value=[exit_10, exit_12])
        rooms[2].get_exits = MagicMock(return_value=[exit_21])

        # Mock ObjectManager
        class MockObjMgr:
            def get(self, obj_id):
                for room in rooms:
                    if room.id == obj_id:
                        return room
                return None

        # 创建寻路器
        finder = PathFinder(MockObjMgr())

        # 测试直接路径
        path = await finder.find_path(rooms[0], rooms[2])
        assert path is not None, "应该找到路径"
        assert len(path) == 2, f"应该需要2步，实际{len(path)}"
        assert path[0][0] == "e", "第一步应该向东"
        assert path[1][0] == "e", "第二步应该向东"

        # 测试同房间
        path = await finder.find_path(rooms[1], rooms[1])
        assert len(path) == 0, "同房间路径应为空"


class TestCrossSystemIntegration:
    """跨系统交互集成测试."""

    @pytest.mark.asyncio
    async def test_equipment_affects_combat_stats(self, game_engine: GameEngine):
        """测试装备影响战斗属性."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="侠客",
            attributes={
                "level": 20,
                "attributes": {"strength": 20, "agility": 15, "constitution": 18, "spirit": 12},
            },
        )

        # 基础属性（力量20*2=40攻击，体质18=18防御）
        base_attack = character.get_attack()  # 40
        base_defense = character.get_defense()  # 18

        # 装备武器
        sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="青锋剑",
            location=character,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "stats_bonus": {"attack": 50, "agility": 10},
            },
        )
        await character.equipment_equip(sword)

        # 装备护甲
        armor = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="铁甲",
            location=character,
            attributes={
                "slot": EquipmentSlot.BODY.value,
                "stats_bonus": {"defense": 40},
            },
        )
        await character.equipment_equip(armor)

        # 验证装备加成通过 get_total_stats
        total_stats = character.equipment_get_stats()
        assert total_stats.get("attack") == 50
        assert total_stats.get("defense") == 40
        assert total_stats.get("agility") == 10

        # 攻击防御现在包含装备加成（通过get_attack/get_defense计算）
        assert character.get_attack() == base_attack + 50  # 40 + 50
        assert character.get_defense() == base_defense + 40  # 18 + 40

    @pytest.mark.asyncio
    async def test_menpai_equipment_restriction(self, game_engine: GameEngine):
        """测试门派装备限制."""
        # 少林弟子
        shaolin_disciple = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="少林弟子",
            attributes={"level": 20, "menpai": "少林派"},
        )

        # 少林专属武器
        shaolin_staff = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="少林棍",
            location=shaolin_disciple,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "menpai_requirement": "少林派",
            },
        )

        # 武当专属武器
        wudang_sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="武当剑",
            location=shaolin_disciple,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "menpai_requirement": "武当派",
            },
        )

        # 可以装备本门派武器
        can_equip, _ = shaolin_staff.can_equip_by(shaolin_disciple)
        assert can_equip is True

        # 不能装备其他门派武器
        can_equip, reason = wudang_sword.can_equip_by(shaolin_disciple)
        assert can_equip is False
        assert "武当派" in reason  # 错误消息包含门派名称

    @pytest.mark.asyncio
    async def test_wuxue_menpai_restriction(self, game_engine: GameEngine):
        """测试武学门派限制."""
        character = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="门派弟子",
            attributes={"menpai": "峨眉派", "level": 20, "birth_talents": {"wuxing": 20}},
        )

        # 本门派武功
        emei_kungfu = Kungfu(
            key="峨眉剑法",
            name="峨眉剑法",
            wuxue_type=WuxueType.JIAN,
            menpai="峨眉派",
            requirements={"level": 10, "wuxing": 15},
            moves=[Move(key="金针渡劫", name="金针渡劫", wuxue_type=WuxueType.JIAN, mp_cost=15)],
        )

        # 其他门派武功
        shaolin_kungfu = Kungfu(
            key="少林棍法",
            name="少林棍法",
            wuxue_type=WuxueType.GUN,
            menpai="少林派",
            requirements={"level": 10, "wuxing": 15},
            moves=[Move(key="横扫千军", name="横扫千军", wuxue_type=WuxueType.GUN, mp_cost=20)],
        )

        # 可以学习本门派武功
        can_learn, _ = emei_kungfu.can_learn(character)
        assert can_learn is True

        # 不能学习其他门派武功
        can_learn, _ = shaolin_kungfu.can_learn(character)
        assert can_learn is False

    @pytest.mark.asyncio
    async def test_full_combat_scenario(self, game_engine: GameEngine):
        """测试完整战斗场景."""
        # 创建两个角色
        attacker = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="攻击者",
            attributes={
                "level": 15,
                "menpai": "丐帮",
                "attributes": {"strength": 25, "agility": 20},
            },
        )

        defender = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="防御者",
            attributes={
                "level": 15,
                "menpai": "全真教",
                "attributes": {"strength": 18, "constitution": 22},
            },
        )

        # 给攻击者装备武器
        sword = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="打狗棒",
            location=attacker,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "stats_bonus": {"attack": 30},
            },
        )
        await attacker.equipment_equip(sword)

        # 给防御者装备护甲
        armor = await game_engine.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="道袍",
            location=defender,
            attributes={
                "slot": EquipmentSlot.BODY.value,
                "stats_bonus": {"defense": 25},
            },
        )
        await defender.equipment_equip(armor)

        # 验证战斗属性
        assert attacker.get_attack() > 0
        assert defender.get_defense() > 0

        # 验证装备加成
        assert attacker.equipment_get_stats().get("attack") == 30
        assert defender.equipment_get_stats().get("defense") == 25

        # 学习武功
        kungfu = Kungfu(
            key="降龙十八掌",
            name="降龙十八掌",
            wuxue_type=WuxueType.ZHANG,
            menpai="丐帮",
            requirements={"level": 10},
            moves=[Move(key="亢龙有悔", name="亢龙有悔", wuxue_type=WuxueType.ZHANG, mp_cost=30)],
        )
        await attacker.wuxue_learn(kungfu)

        # 验证武功学习成功
        assert attacker.wuxue_has_learned("降龙十八掌") is True


class TestPersistence:
    """数据持久化集成测试."""

    @pytest.mark.asyncio
    async def test_character_persistence(self, tmp_path: Path):
        """测试角色数据持久化."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'persist.db'}"

        # 第一次会话
        engine1 = GameEngine(config)
        await engine1.initialize()
        await engine1.start()

        character = await engine1.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="存档测试",
            attributes={
                "level": 25,
                "exp": 5000,
                "menpai": "华山派",
                "birth_talents": {"gengu": 28, "wuxing": 25, "fuyuan": 20, "rongmao": 22},
            },
        )

        # 创建装备并穿戴
        sword = await engine1.objects.create(
            typeclass_path="src.game.typeclasses.equipment.Equipment",
            key="存档剑",
            location=character,
            attributes={
                "slot": EquipmentSlot.MAIN_HAND.value,
                "quality": EquipmentQuality.RARE.value,
                "stats_bonus": {"attack": 100},
            },
        )
        await character.equipment_equip(sword)

        char_id = character.id
        await engine1.stop()

        # 第二次会话
        engine2 = GameEngine(config)
        await engine2.initialize()

        loaded = await engine2.objects.load(char_id)
        assert loaded is not None
        assert loaded.key == "存档测试"
        assert loaded.level == 25
        assert loaded.menpai == "华山派"
        assert loaded.birth_talents["gengu"] == 28

        await engine2.stop()

    @pytest.mark.asyncio
    async def test_room_persistence(self, tmp_path: Path):
        """测试房间数据持久化."""
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{tmp_path / 'room_persist.db'}"

        engine1 = GameEngine(config)
        await engine1.initialize()
        await engine1.start()

        room = await engine1.objects.create(
            typeclass_path="src.game.typeclasses.room.Room",
            key="持久化房间",
            attributes={
                "coords": [10, 20, 0],  # JSON 会保存为 list
                "area": "测试区域",
                "description": "这是一个测试房间。",
            },
        )

        room_id = room.id
        await engine1.stop()

        # 重新加载
        engine2 = GameEngine(config)
        await engine2.initialize()

        loaded = await engine2.objects.load(room_id)
        assert loaded is not None
        # coords 从 JSON 加载后是 list，需要比较时转换
        coords = loaded.coords
        assert list(coords) == [10, 20, 0]
        assert loaded.area == "测试区域"

        await engine2.stop()

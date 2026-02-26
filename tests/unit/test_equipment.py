"""Equipment 装备系统单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import (
    SLOT_NAMES,
    Equipment,
    EquipmentQuality,
    EquipmentSlot,
)


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_item")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.game.typeclasses.equipment.Equipment"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self) -> None:
        self._cache: dict[int, Equipment] = {}
        self.dirty_objects: set[int] = set()

    def get(self, obj_id: int) -> Equipment | None:
        return self._cache.get(obj_id)

    def mark_dirty(self, obj: Equipment) -> None:
        self.dirty_objects.add(obj.id)

    def mark_dirty(self, obj: Equipment) -> None:
        self.dirty_objects.add(obj.id)


@pytest.fixture
def manager():
    """创建共享的管理器."""
    return MockManager()


@pytest.fixture
def equipment(manager):
    """创建测试装备."""
    db_model = MockDBModel(id=1, key="精铁长剑")
    equip = Equipment(manager, db_model)
    return equip


@pytest.fixture
def character(manager):
    """创建测试角色."""
    from src.game.typeclasses.character import Character as CharClass

    db_model = MockDBModel(id=2, key="张三", typeclass_path=CharClass.typeclass_path)
    char = CharClass(manager, db_model)
    char.level = 10
    char.menpai = "少林"
    return char


class TestEquipmentSlot:
    """装备槽位测试."""

    def test_slot_count(self):
        """测试槽位数量."""
        assert len(EquipmentSlot) == 12

    def test_slot_names(self):
        """测试槽位名称."""
        assert SLOT_NAMES[EquipmentSlot.MAIN_HAND] == "主手"
        assert SLOT_NAMES[EquipmentSlot.HEAD] == "头部"
        assert SLOT_NAMES[EquipmentSlot.BODY] == "身体"


class TestEquipmentQuality:
    """装备品质测试."""

    def test_quality_values(self):
        """测试品质值."""
        assert EquipmentQuality.COMMON == 1
        assert EquipmentQuality.LEGENDARY == 5

    def test_quality_names(self):
        """测试品质名称."""
        from src.game.typeclasses.equipment import QUALITY_NAMES

        assert QUALITY_NAMES[EquipmentQuality.COMMON] == "普通"
        assert QUALITY_NAMES[EquipmentQuality.LEGENDARY] == "传说"


class TestEquipmentProperties:
    """装备属性测试."""

    def test_default_slot(self, equipment: Equipment):
        """测试默认槽位."""
        assert equipment.slot == EquipmentSlot.MAIN_HAND

    def test_set_slot(self, equipment: Equipment):
        """测试设置槽位."""
        equipment.slot = EquipmentSlot.HEAD
        assert equipment.slot == EquipmentSlot.HEAD

    def test_default_quality(self, equipment: Equipment):
        """测试默认品质."""
        assert equipment.quality == EquipmentQuality.COMMON

    def test_set_quality(self, equipment: Equipment):
        """测试设置品质."""
        equipment.quality = EquipmentQuality.EPIC
        assert equipment.quality == EquipmentQuality.EPIC
        assert equipment.quality_name == "史诗"

    def test_stats_bonus(self, equipment: Equipment):
        """测试属性加成."""
        equipment.stats_bonus = {"attack": 25, "strength": 3}
        assert equipment.stats_bonus["attack"] == 25
        assert equipment.stats_bonus["strength"] == 3

    def test_durability(self, equipment: Equipment):
        """测试耐久度."""
        equipment.durability = (80, 100)
        assert equipment.durability == (80, 100)

    def test_modify_durability(self, equipment: Equipment):
        """测试修改耐久度."""
        equipment.durability = (100, 100)
        current = equipment.modify_durability(-20)
        assert current == 80
        assert equipment.durability == (80, 100)

    def test_modify_durability_not_below_zero(self, equipment: Equipment):
        """测试耐久度不会低于0."""
        equipment.durability = (10, 100)
        current = equipment.modify_durability(-50)
        assert current == 0

    def test_is_broken(self, equipment: Equipment):
        """测试损坏状态."""
        equipment.durability = (0, 100)
        assert equipment.is_broken

    def test_is_not_broken(self, equipment: Equipment):
        """测试未损坏状态."""
        equipment.durability = (1, 100)
        assert not equipment.is_broken

    def test_bind(self, equipment: Equipment):
        """测试绑定."""
        assert not equipment.is_bound
        equipment.bind()
        assert equipment.is_bound

    def test_set_name(self, equipment: Equipment):
        """测试套装名称."""
        equipment.set_name = "少林套装"
        assert equipment.set_name == "少林套装"

    def test_level_requirement(self, equipment: Equipment):
        """测试等级要求."""
        equipment.level_requirement = 15
        assert equipment.level_requirement == 15

    def test_menpai_requirement(self, equipment: Equipment):
        """测试门派要求."""
        equipment.menpai_requirement = "武当"
        assert equipment.menpai_requirement == "武当"


class TestEquipmentCanEquip:
    """装备条件检查测试."""

    def test_can_equip_meets_requirements(self, equipment: Equipment, character):
        """测试满足条件时可以装备."""
        equipment.level_requirement = 5
        can_equip, reason = equipment.can_equip_by(character)
        assert can_equip
        assert reason == ""

    def test_cannot_equip_level_too_low(self, equipment: Equipment, character):
        """测试等级不足时不能装备."""
        equipment.level_requirement = 20
        can_equip, reason = equipment.can_equip_by(character)
        assert not can_equip
        assert "等级不足" in reason

    def test_cannot_equip_wrong_menpai(self, equipment: Equipment, character):
        """测试门派不符时不能装备."""
        equipment.menpai_requirement = "武当"
        can_equip, reason = equipment.can_equip_by(character)
        assert not can_equip
        assert "仅限" in reason

    def test_can_equip_right_menpai(self, equipment: Equipment, character):
        """测试门派相符时可以装备."""
        equipment.menpai_requirement = "少林"
        can_equip, reason = equipment.can_equip_by(character)
        assert can_equip


class TestCharacterEquipmentMixin:
    """角色装备管理测试."""

    def test_default_equipped_empty(self, character):
        """测试默认装备栏为空."""
        assert character.equipment_slots == {}

    @pytest.mark.asyncio
    async def test_equip_success(self, character, equipment):
        """测试装备成功."""
        # 设置装备在角色背包中
        # 确保 character 在 cache 中，并且 equipment 的 location 指向 character
        character._manager._cache[character.id] = character
        character._manager._cache[equipment.id] = equipment
        
        # 设置装备的 location 为 character
        equipment._db_model.location_id = character.id

        success, msg = await character.equipment_equip(equipment)
        assert success, f"装备失败: {msg}"
        assert "装备成功" in msg
        assert character.equipment_slots[EquipmentSlot.MAIN_HAND.value] == equipment.id

    @pytest.mark.asyncio
    async def test_equip_not_in_inventory(self, character, equipment):
        """测试不在背包中时不能装备."""
        equipment._db_model.location_id = None  # 不在背包中
        success, msg = await character.equipment_equip(equipment)
        assert not success
        assert "物品不在背包中" in msg

    @pytest.mark.asyncio
    async def test_unequip_success(self, character, equipment):
        """测试卸下装备成功."""
        # 先装备
        character._manager._cache[character.id] = character
        character._manager._cache[equipment.id] = equipment
        equipment._db_model.location_id = character.id

        success, _ = await character.equipment_equip(equipment)
        assert success, "装备应该成功"
        
        success, msg = await character.equipment_unequip(EquipmentSlot.MAIN_HAND)
        assert success
        assert "卸下成功" in msg
        assert EquipmentSlot.MAIN_HAND.value not in character.equipment_slots

    @pytest.mark.asyncio
    async def test_unequip_not_equipped(self, character):
        """测试卸下未装备的槽位失败."""
        success, msg = await character.equipment_unequip(EquipmentSlot.MAIN_HAND)
        assert not success
        assert "该槽位未装备物品" in msg

    @pytest.mark.asyncio
    async def test_get_total_stats(self, character, equipment):
        """测试计算总属性."""
        equipment.stats_bonus = {"attack": 25, "strength": 3}
        character._manager._cache[character.id] = character
        character._manager._cache[equipment.id] = equipment

        # 装备
        equipment._db_model.location_id = character.id
        success, _ = await character.equipment_equip(equipment)
        assert success, "装备应该成功"

        total = character.equipment_get_stats()
        assert total["attack"] == 25
        assert total["strength"] == 3

    @pytest.mark.asyncio
    async def test_get_total_stats_excludes_broken(self, character, equipment):
        """测试损坏装备不计入属性."""
        equipment.stats_bonus = {"attack": 25}
        equipment.durability = (0, 100)  # 损坏
        character._manager._cache[equipment.id] = equipment
        character._manager._cache[character.id] = character

        equipment._db_model.location_id = character.id
        await character.equipment_equip(equipment)

        total = character.equipment_get_stats()
        assert total.get("attack", 0) == 0

    @pytest.mark.asyncio
    async def test_equip_binds_item(self, character, equipment):
        """测试装备时自动绑定."""
        character._manager._cache[character.id] = character
        character._manager._cache[equipment.id] = equipment
        equipment._db_model.location_id = character.id

        assert not equipment.is_bound
        success, _ = await character.equipment_equip(equipment)
        assert success, "装备应该成功"
        assert equipment.is_bound


class TestEquipmentDesc:
    """装备描述测试."""

    def test_get_desc_contains_basic_info(self, equipment: Equipment):
        """测试描述包含基本信息."""
        equipment.quality = EquipmentQuality.RARE
        desc = equipment.get_desc()
        assert "精铁长剑" in desc
        assert "精良" in desc

    def test_get_desc_contains_stats(self, equipment: Equipment):
        """测试描述包含属性."""
        equipment.stats_bonus = {"attack": 25}
        desc = equipment.get_desc()
        assert "attack" in desc
        assert "25" in desc

    def test_get_desc_contains_set_name(self, equipment: Equipment):
        """测试描述包含套装信息."""
        equipment.set_name = "少林套装"
        desc = equipment.get_desc()
        assert "少林套装" in desc

    def test_get_desc_shows_bound(self, equipment: Equipment):
        """测试描述显示绑定状态."""
        equipment.bind()
        desc = equipment.get_desc()
        assert "已绑定" in desc

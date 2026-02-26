"""Character 角色系统单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_char")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.game.typeclasses.character.Character"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self) -> None:
        self._cache: dict[int, Character] = {}
        self.dirty_objects: set[int] = set()

    def mark_dirty(self, obj: Character) -> None:
        """标记对象为脏数据."""
        self.dirty_objects.add(obj.id)


@pytest.fixture
def mock_manager():
    """创建模拟管理器."""
    return MockManager()


@pytest.fixture
def mock_db_model():
    """创建模拟数据库模型."""
    return MockDBModel()


@pytest.fixture
def character(mock_manager, mock_db_model):
    """创建测试角色."""
    return Character(mock_manager, mock_db_model)


class TestCharacterName:
    """角色名称属性测试."""

    def test_name_defaults_to_key(self, mock_manager, mock_db_model):
        """测试 name 默认值回退到 key."""
        char = Character(mock_manager, mock_db_model)
        # 没有设置 name，应该返回 key
        assert char.name == char.key

    def test_name_custom_value(self, mock_manager, mock_db_model):
        """测试自定义 name."""
        char = Character(mock_manager, mock_db_model)
        char.name = "王铁匠"
        assert char.name == "王铁匠"
        assert char.key != "王铁匠"  # key 不变

    def test_name_empty_string_fallback(self, mock_manager, mock_db_model):
        """测试空字符串回退到 key."""
        char = Character(mock_manager, mock_db_model)
        char.db.set("name", "")  # 设置空字符串
        assert char.name == char.key  # 应该回退到 key

    def test_name_persistence(self, mock_manager, mock_db_model):
        """测试 name 持久化到 attributes."""
        char = Character(mock_manager, mock_db_model)
        char.name = "测试名称"
        # 验证存储在 db 中
        assert char.db.get("name") == "测试名称"

    def test_name_none_fallback(self, mock_manager, mock_db_model):
        """测试 None 值回退到 key."""
        char = Character(mock_manager, mock_db_model)
        char.db.set("name", None)
        assert char.name == char.key


class TestCharacterBirthTalents:
    """先天资质测试."""

    def test_default_birth_talents(self, character: Character):
        """测试默认先天资质."""
        talents = character.birth_talents
        assert talents["gengu"] == 15
        assert talents["wuxing"] == 15
        assert talents["fuyuan"] == 15
        assert talents["rongmao"] == 15

    def test_set_birth_talents(self, character: Character):
        """测试设置先天资质."""
        character.birth_talents = {
            "gengu": 20,
            "wuxing": 18,
            "fuyuan": 16,
            "rongmao": 17,
        }
        assert character.gengu == 20
        assert character.wuxing == 18
        assert character.fuyuan == 16
        assert character.rongmao == 17

    def test_convenience_properties(self, character: Character):
        """测试便捷属性访问."""
        character.birth_talents = {"gengu": 25}
        assert character.gengu == 25


class TestCharacterAttributes:
    """后天属性测试."""

    def test_default_attributes(self, character: Character):
        """测试默认后天属性."""
        attrs = character.attributes
        assert attrs["strength"] == 10
        assert attrs["agility"] == 10
        assert attrs["constitution"] == 10
        assert attrs["spirit"] == 10

    def test_set_attributes(self, character: Character):
        """测试设置后天属性."""
        character.attributes = {
            "strength": 15,
            "agility": 12,
            "constitution": 14,
            "spirit": 11,
        }
        assert character.attributes["strength"] == 15


class TestCharacterStatus:
    """动态状态测试."""

    def test_default_status(self, character: Character):
        """测试默认状态 - 使用属性计算的最大值."""
        # HP = 基础100 + 体质*10 + 根骨*5 = 100 + 100 + 75 = 275
        assert character.get_hp() == (275, 275)
        # MP = 基础50 + 精神*8 + 根骨*3 = 50 + 80 + 45 = 175
        assert character.get_mp() == (175, 175)

    def test_get_hp(self, character: Character):
        """测试获取气血."""
        character.status = {"hp": (80, 100)}
        assert character.get_hp() == (80, 100)

    def test_modify_hp_positive(self, character: Character):
        """测试增加气血."""
        character.status = {"hp": (50, 100)}
        delta = character.modify_hp(20)
        assert delta == 20
        assert character.get_hp()[0] == 70

    def test_modify_hp_negative(self, character: Character):
        """测试减少气血."""
        character.status = {"hp": (50, 100)}
        delta = character.modify_hp(-20)
        assert delta == -20
        assert character.get_hp()[0] == 30

    def test_modify_hp_not_below_zero(self, character: Character):
        """测试气血不会低于0."""
        character.status = {"hp": (10, 100)}
        delta = character.modify_hp(-50)
        assert delta == -10  # 实际只能减少10
        assert character.get_hp()[0] == 0

    def test_modify_hp_not_above_max(self, character: Character):
        """测试气血不会超过上限."""
        character.status = {"hp": (90, 100)}
        delta = character.modify_hp(20)
        assert delta == 10  # 实际只能增加10
        assert character.get_hp()[0] == 100

    def test_modify_mp(self, character: Character):
        """测试修改内力."""
        character.status = {"mp": (30, 50)}
        character.modify_mp(10)
        assert character.get_mp()[0] == 40


class TestCharacterCombatStats:
    """战斗属性计算测试."""

    def test_get_max_hp_calculation(self, character: Character):
        """测试最大气血计算."""
        # 基础 100 + 体质*10 + 根骨*5
        character.attributes = {"constitution": 15}
        character.birth_talents = {"gengu": 20}
        # 100 + 15*10 + 20*5 = 100 + 150 + 100 = 350
        expected = 100 + 15 * 10 + 20 * 5
        assert character.get_max_hp() == expected

    def test_get_max_mp_calculation(self, character: Character):
        """测试最大内力计算."""
        # 基础 50 + 精神*8 + 根骨*3
        character.attributes = {"spirit": 12}
        character.birth_talents = {"gengu": 18}
        # 50 + 12*8 + 18*3 = 50 + 96 + 54 = 200
        expected = 50 + 12 * 8 + 18 * 3
        assert character.get_max_mp() == expected

    def test_get_attack(self, character: Character):
        """测试攻击力计算."""
        character.attributes = {"strength": 15}
        # 基础 力量*2 = 15*2 = 30
        assert character.get_attack() == 30

    def test_get_defense(self, character: Character):
        """测试防御力计算."""
        character.attributes = {"constitution": 14}
        # 基础 体质 = 14
        assert character.get_defense() == 14

    def test_get_agility(self, character: Character):
        """测试敏捷计算."""
        character.attributes = {"agility": 16}
        # 基础 敏捷 = 16
        assert character.get_agility() == 16


class TestCharacterLeveling:
    """角色成长测试."""

    def test_default_level(self, character: Character):
        """测试默认等级."""
        assert character.level == 1

    def test_default_exp(self, character: Character):
        """测试默认经验."""
        assert character.exp == 0

    def test_add_exp_no_level_up(self, character: Character):
        """测试增加经验但不升级."""
        character.level = 1
        character.exp = 50
        leveled_up = character.add_exp(40)  # 需要 400 才升到2级
        assert not leveled_up
        assert character.level == 1
        assert character.exp == 90

    def test_add_exp_with_level_up(self, character: Character):
        """测试增加经验并升级."""
        character.level = 1
        character.exp = 350  # 需要 400 升到2级
        leveled_up = character.add_exp(60)  # 超过 400，升级
        assert leveled_up
        assert character.level == 2

    def test_get_exp_for_level(self, character: Character):
        """测试获取升级所需经验."""
        # 等级 n 需要 n*n*100 经验
        assert character._get_exp_for_level(2) == 400  # 2*2*100
        assert character._get_exp_for_level(3) == 900  # 3*3*100

    def test_recalculate_status_on_level_up(self, character: Character):
        """测试升级时重新计算状态."""
        character.level = 1
        character.status = {"hp": (50, 100), "mp": (25, 50)}
        character.level_up()
        # 升级后状态应该被重新计算
        hp = character.get_hp()
        assert hp[0] == hp[1]  # 满血


class TestCharacterMenpai:
    """门派系统测试."""

    def test_default_menpai(self, character: Character):
        """测试默认门派."""
        assert character.menpai is None

    def test_set_menpai(self, character: Character):
        """测试设置门派."""
        character.menpai = "少林"
        assert character.menpai == "少林"

    def test_menpai_contrib(self, character: Character):
        """测试门派贡献."""
        assert character.menpai_contrib == 0
        character.menpai_contrib = 100
        assert character.menpai_contrib == 100
        character.add_contrib(50)
        assert character.menpai_contrib == 150


class TestCharacterInternalPower:
    """内力系统测试."""

    def test_default_internal_type(self, character: Character):
        """测试默认内力属性."""
        assert character.internal_type == "neutral"

    def test_set_internal_type(self, character: Character):
        """测试设置内力属性."""
        character.internal_type = "yang"
        assert character.internal_type == "yang"

    def test_default_meridians(self, character: Character):
        """测试默认经脉状态."""
        assert character.meridians == {}


class TestCharacterDeath:
    """死亡处理测试."""

    def test_death_exp_loss(self, character: Character):
        """测试死亡时扣除经验."""
        character.level = 5
        character.exp = 1000
        character.at_death()
        assert character.exp == 900  # 扣除 1000 // 10 = 100

    def test_death_exp_not_below_zero(self, character: Character):
        """测试死亡时经验不会低于0."""
        character.exp = 50
        character.at_death()
        # 扣除 50 // 10 = 5，剩余 45
        assert character.exp == 45

    def test_death_restore_status(self, character: Character):
        """测试死亡后恢复状态."""
        character.status = {"hp": (0, 100), "mp": (0, 50), "ep": (0, 100)}
        character.at_death()
        hp = character.get_hp()
        assert hp[0] > 0  # 恢复了一些气血

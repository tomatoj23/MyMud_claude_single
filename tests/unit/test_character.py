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

    def get(self, obj_id: int) -> Character | None:
        return self._cache.get(obj_id)

    def mark_dirty(self, obj: Character) -> None:
        self.dirty_objects.add(obj.id)

    def mark_dirty(self, obj: Character) -> None:
        self.dirty_objects.add(obj.id)


@pytest.fixture
def character():
    """创建测试角色."""
    manager = MockManager()
    db_model = MockDBModel(id=1, key="张三")
    char = Character(manager, db_model)
    return char


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
        character.birth_talents = {"gengu": 20, "wuxing": 18, "fuyuan": 12, "rongmao": 10}
        assert character.gengu == 20
        assert character.wuxing == 18
        assert character.fuyuan == 12
        assert character.rongmao == 10

    def test_convenience_properties(self, character: Character):
        """测试便捷属性访问."""
        character.birth_talents = {"gengu": 25, "wuxing": 20, "fuyuan": 15, "rongmao": 12}
        assert character.gengu == 25
        assert character.wuxing == 20


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
        character.attributes = {"strength": 15, "agility": 12, "constitution": 14, "spirit": 11}
        assert character.attributes["strength"] == 15


class TestCharacterStatus:
    """动态状态测试."""

    def test_default_status(self, character: Character):
        """测试默认状态（at_init 会根据属性计算）."""
        status = character.status
        # at_init 会调用 _recalculate_status，所以不是默认值
        # 而是根据属性计算的值
        assert status["hp"][0] > 0  # 当前气血 > 0
        assert status["mp"][0] > 0  # 当前内力 > 0

    def test_get_hp(self, character: Character):
        """测试获取气血."""
        hp = character.get_hp()
        # at_init 会重新计算状态
        assert hp[0] > 0  # 当前气血
        assert hp[1] > 0  # 最大气血

    def test_modify_hp_positive(self, character: Character):
        """测试增加气血."""
        character.status = {"hp": (50, 100), "mp": (50, 50), "ep": (100, 100)}
        delta = character.modify_hp(30)
        assert delta == 30
        assert character.get_hp() == (80, 100)

    def test_modify_hp_negative(self, character: Character):
        """测试减少气血（受伤）."""
        character.status = {"hp": (100, 100), "mp": (50, 50), "ep": (100, 100)}
        delta = character.modify_hp(-30)
        assert delta == -30
        assert character.get_hp() == (70, 100)

    def test_modify_hp_not_below_zero(self, character: Character):
        """测试气血不会低于0."""
        character.status = {"hp": (20, 100), "mp": (50, 50), "ep": (100, 100)}
        delta = character.modify_hp(-50)
        assert delta == -20  # 实际只能减少20
        assert character.get_hp() == (0, 100)

    def test_modify_hp_not_above_max(self, character: Character):
        """测试气血不会超过最大值."""
        character.status = {"hp": (80, 100), "mp": (50, 50), "ep": (100, 100)}
        delta = character.modify_hp(50)
        assert delta == 20  # 实际只能增加20
        assert character.get_hp() == (100, 100)

    def test_modify_mp(self, character: Character):
        """测试修改内力."""
        character.status = {"hp": (100, 100), "mp": (30, 50), "ep": (100, 100)}
        delta = character.modify_mp(-10)
        assert delta == -10
        assert character.get_mp() == (20, 50)


class TestCharacterCombatStats:
    """战斗属性计算测试."""

    def test_get_max_hp_calculation(self, character: Character):
        """测试最大气血计算."""
        # 基础100 + 体质*10 + 根骨*5
        character.attributes = {"strength": 10, "agility": 10, "constitution": 15, "spirit": 10}
        character.birth_talents = {"gengu": 20, "wuxing": 15, "fuyuan": 15, "rongmao": 15}
        # 100 + 15*10 + 20*5 = 100 + 150 + 100 = 350
        assert character.get_max_hp() == 350

    def test_get_max_mp_calculation(self, character: Character):
        """测试最大内力计算."""
        # 基础50 + 精神*8 + 根骨*3
        character.attributes = {"strength": 10, "agility": 10, "constitution": 10, "spirit": 15}
        character.birth_talents = {"gengu": 20, "wuxing": 15, "fuyuan": 15, "rongmao": 15}
        # 50 + 15*8 + 20*3 = 50 + 120 + 60 = 230
        assert character.get_max_mp() == 230

    def test_get_attack(self, character: Character):
        """测试攻击力计算."""
        character.attributes = {"strength": 15, "agility": 10, "constitution": 10, "spirit": 10}
        # 力量 * 2 = 15 * 2 = 30
        assert character.get_attack() == 30

    def test_get_defense(self, character: Character):
        """测试防御力计算."""
        character.attributes = {"strength": 10, "agility": 10, "constitution": 15, "spirit": 10}
        # 体质 = 15
        assert character.get_defense() == 15

    def test_get_agility(self, character: Character):
        """测试敏捷计算."""
        character.attributes = {"strength": 10, "agility": 18, "constitution": 10, "spirit": 10}
        # 敏捷 = 18
        assert character.get_agility() == 18


class TestCharacterLeveling:
    """角色成长测试."""

    def test_default_level(self, character: Character):
        """测试默认等级."""
        assert character.level == 1

    def test_default_exp(self, character: Character):
        """测试默认经验."""
        assert character.exp == 0

    def test_add_exp_no_level_up(self, character: Character):
        """测试增加经验但不足以升级."""
        character.level = 1
        character.exp = 0
        leveled = character.add_exp(50)  # 需要 2*2*100=400 才能升到2级
        assert not leveled
        assert character.level == 1
        assert character.exp == 50

    def test_add_exp_with_level_up(self, character: Character):
        """测试增加经验并升级."""
        character.level = 1
        character.exp = 350
        leveled = character.add_exp(100)  # 总共450，超过400
        assert leveled
        assert character.level == 2

    def test_get_exp_for_level(self, character: Character):
        """测试升级所需经验计算."""
        # level * level * 100
        assert character._get_exp_for_level(2) == 400
        assert character._get_exp_for_level(3) == 900
        assert character._get_exp_for_level(10) == 10000

    def test_recalculate_status_on_level_up(self, character: Character):
        """测试升级时重新计算状态."""
        character.level = 1
        character.attributes = {"strength": 15, "agility": 10, "constitution": 20, "spirit": 10}
        character.birth_talents = {"gengu": 20, "wuxing": 15, "fuyuan": 15, "rongmao": 15}
        character.exp = 400
        character.add_exp(0)  # 触发升级检查

        # 升级后应该满血满蓝
        hp = character.get_hp()
        assert hp[0] == hp[1]  # 当前值等于最大值


class TestCharacterMenpai:
    """门派系统测试."""

    def test_default_menpai(self, character: Character):
        """测试默认门派（无）."""
        assert character.menpai is None

    def test_set_menpai(self, character: Character):
        """测试设置门派."""
        character.menpai = "少林"
        assert character.menpai == "少林"

    def test_menpai_contrib(self, character: Character):
        """测试门派贡献."""
        assert character.menpai_contrib == 0
        character.add_contrib(100)
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

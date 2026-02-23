"""武侠角色类型.

属性结构：
- 先天资质：birth_talents {gengu, wuxing, fuyuan, rongmao}
- 后天属性：attributes {strength, agility, constitution, spirit}
- 动态状态：status {hp, mp, ep}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.engine.core.typeclass import TypeclassBase
from src.game.typeclasses.equipment import CharacterEquipmentMixin
from src.game.typeclasses.wuxue import CharacterWuxueMixin

if TYPE_CHECKING:
    pass


class Character(CharacterEquipmentMixin, CharacterWuxueMixin, TypeclassBase):
    """武侠角色类型.

    Attributes:
        typeclass_path: 类型路径
    """

    typeclass_path = "src.game.typeclasses.character.Character"

    # ===== 先天资质（创建时随机，1-30，几乎不变） =====
    @property
    def birth_talents(self) -> dict[str, int]:
        """先天资质.

        Returns:
            {
                "gengu": 根骨 - 影响体质、气血上限,
                "wuxing": 悟性 - 影响武学领悟速度,
                "fuyuan": 福缘 - 影响奇遇概率,
                "rongmao": 容貌 - 影响NPC态度,
            }
        """
        return self.db.get(
            "birth_talents",
            {
                "gengu": 15,
                "wuxing": 15,
                "fuyuan": 15,
                "rongmao": 15,
            },
        )

    @birth_talents.setter
    def birth_talents(self, value: dict[str, int]) -> None:
        self.db.set("birth_talents", value)

    # 便捷访问
    @property
    def gengu(self) -> int:
        """根骨."""
        return self.birth_talents.get("gengu", 15)

    @property
    def wuxing(self) -> int:
        """悟性."""
        return self.birth_talents.get("wuxing", 15)

    @property
    def fuyuan(self) -> int:
        """福缘."""
        return self.birth_talents.get("fuyuan", 15)

    @property
    def rongmao(self) -> int:
        """容貌."""
        return self.birth_talents.get("rongmao", 15)

    # ===== 后天属性（可通过修炼提升） =====
    @property
    def attributes(self) -> dict[str, int]:
        """后天属性.

        Returns:
            {
                "strength": 力量 - 影响外功伤害,
                "agility": 敏捷 - 影响闪避、命中,
                "constitution": 体质 - 影响气血上限,
                "spirit": 精神 - 影响内力上限、抗性,
            }
        """
        return self.db.get(
            "attributes",
            {
                "strength": 10,
                "agility": 10,
                "constitution": 10,
                "spirit": 10,
            },
        )

    @attributes.setter
    def attributes(self, value: dict[str, int]) -> None:
        self.db.set("attributes", value)

    # ===== 动态状态（战斗中实时变化） =====
    @property
    def status(self) -> dict[str, tuple[int, int]]:
        """动态状态 - (当前值, 最大值).

        Returns:
            {
                "hp": (当前气血, 最大气血),
                "mp": (当前内力, 最大内力),
                "ep": (当前精力, 最大精力),
            }
        """
        default = {
            "hp": (100, 100),
            "mp": (50, 50),
            "ep": (100, 100),
        }
        return self.db.get("status", default)

    @status.setter
    def status(self, value: dict[str, tuple[int, int]]) -> None:
        self.db.set("status", value)

    # ===== 状态访问方法 =====
    def get_hp(self) -> tuple[int, int]:
        """获取当前/最大气血."""
        return self.status.get("hp", (100, 100))

    def modify_hp(self, delta: int) -> int:
        """修改气血，返回实际变化值.

        Args:
            delta: 变化值（正为治疗，负为伤害）

        Returns:
            实际变化值
        """
        current, max_hp = self.get_hp()
        new_hp = max(0, min(current + delta, max_hp))
        actual_delta = new_hp - current

        status = self.status
        status["hp"] = (new_hp, max_hp)
        self.status = status

        return actual_delta

    def get_mp(self) -> tuple[int, int]:
        """获取当前/最大内力."""
        return self.status.get("mp", (50, 50))

    def modify_mp(self, delta: int) -> int:
        """修改内力，返回实际变化值."""
        current, max_mp = self.get_mp()
        new_mp = max(0, min(current + delta, max_mp))
        actual_delta = new_mp - current

        status = self.status
        status["mp"] = (new_mp, max_mp)
        self.status = status

        return actual_delta

    def get_ep(self) -> tuple[int, int]:
        """获取当前/最大精力."""
        return self.status.get("ep", (100, 100))

    def modify_ep(self, delta: int) -> int:
        """修改精力，返回实际变化值."""
        current, max_ep = self.get_ep()
        new_ep = max(0, min(current + delta, max_ep))
        actual_delta = new_ep - current

        status = self.status
        status["ep"] = (new_ep, max_ep)
        self.status = status

        return actual_delta

    # ===== 属性计算 =====
    def get_max_hp(self) -> int:
        """计算最大气血 = 基础值 + 体质*10 + 根骨*5."""
        base = 100
        from_constitution = self.attributes.get("constitution", 10) * 10
        from_gengu = self.gengu * 5
        return base + from_constitution + from_gengu

    def get_max_mp(self) -> int:
        """计算最大内力 = 基础值 + 精神*8 + 根骨*3."""
        base = 50
        from_spirit = self.attributes.get("spirit", 10) * 8
        from_gengu = self.gengu * 3
        return base + from_spirit + from_gengu

    def get_max_ep(self) -> int:
        """计算最大精力 = 基础值100."""
        return 100

    def get_attack(self) -> int:
        """计算攻击力（基础 + 装备 + BUFF）."""
        base = self.attributes.get("strength", 10) * 2
        return base

    def get_defense(self) -> int:
        """计算防御力."""
        base = self.attributes.get("constitution", 10)
        return base

    def get_agility(self) -> int:
        """计算敏捷（影响闪避、命中）."""
        base = self.attributes.get("agility", 10)
        return base

    # ===== 角色成长 =====
    @property
    def level(self) -> int:
        """等级."""
        return self.db.get("level", 1)

    @level.setter
    def level(self, value: int) -> None:
        self.db.set("level", value)

    @property
    def exp(self) -> int:
        """经验值."""
        return self.db.get("exp", 0)

    @exp.setter
    def exp(self, value: int) -> None:
        self.db.set("exp", value)

    def add_exp(self, amount: int) -> bool:
        """增加经验，返回是否升级.

        Args:
            amount: 经验值

        Returns:
            是否升级
        """
        self.exp = self.exp + amount

        # 检查升级
        required = self._get_exp_for_level(self.level + 1)
        if self.exp >= required:
            self.level_up()
            return True
        return False

    def _get_exp_for_level(self, level: int) -> int:
        """获取升级所需经验."""
        return level * level * 100

    def level_up(self) -> None:
        """升级处理."""
        self.level += 1

        # 恢复状态
        self._recalculate_status()

        # 触发升级事件
        self.at_level_up()

    def _recalculate_status(self) -> None:
        """重新计算状态（升级或属性变化时调用）."""
        max_hp = self.get_max_hp()
        max_mp = self.get_max_mp()
        max_ep = self.get_max_ep()

        self.status = {
            "hp": (max_hp, max_hp),  # 满血
            "mp": (max_mp, max_mp),  # 满蓝
            "ep": (max_ep, max_ep),  # 满精力
        }

    # ===== 门派系统 =====
    @property
    def menpai(self) -> Optional[str]:
        """当前门派."""
        return self.db.get("menpai")

    @menpai.setter
    def menpai(self, value: Optional[str]) -> None:
        self.db.set("menpai", value)

    @property
    def menpai_contrib(self) -> int:
        """门派贡献."""
        return self.db.get("menpai_contrib", 0)

    @menpai_contrib.setter
    def menpai_contrib(self, value: int) -> None:
        self.db.set("menpai_contrib", value)

    def add_contrib(self, amount: int) -> None:
        """增加门派贡献."""
        self.menpai_contrib = self.menpai_contrib + amount

    # ===== 内力系统 =====
    @property
    def internal_type(self) -> str:
        """内力属性 - 阴/阳/刚/柔/中性."""
        return self.db.get("internal_type", "neutral")

    @internal_type.setter
    def internal_type(self, value: str) -> None:
        self.db.set("internal_type", value)

    @property
    def meridians(self) -> dict[str, dict]:
        """经脉状态."""
        return self.db.get("meridians", {})

    @meridians.setter
    def meridians(self, value: dict[str, dict]) -> None:
        self.db.set("meridians", value)

    # ===== 生命周期钩子 =====
    def at_level_up(self) -> None:
        """升级时调用（子类可重写）."""
        pass

    def at_death(self) -> None:
        """死亡时调用."""
        # 扣除经验
        exp_loss = self.exp // 10
        self.exp = max(0, self.exp - exp_loss)

        # 恢复状态
        self._recalculate_status()

    def at_init(self) -> None:
        """初始化时调用."""
        # 确保状态已初始化
        if not self.db.get("status"):
            self._recalculate_status()

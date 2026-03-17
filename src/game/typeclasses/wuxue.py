"""武学系统.

包括武功定义、招式系统、学习进度、克制关系.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .character import Character


class WuxueType(Enum):
    """武学类型."""

    QUAN = "quan"  # 拳
    ZHANG = "zhang"  # 掌
    ZHI = "zhi"  # 指
    JIAN = "jian"  # 剑
    DAO = "dao"  # 刀
    GUN = "gun"  # 棍/杖
    NEIGONG = "neigong"  # 内功
    QINGGONG = "qinggong"  # 轻功


WUXUE_TYPE_NAMES = {
    WuxueType.QUAN: "拳法",
    WuxueType.ZHANG: "掌法",
    WuxueType.ZHI: "指法",
    WuxueType.JIAN: "剑法",
    WuxueType.DAO: "刀法",
    WuxueType.GUN: "棍法",
    WuxueType.NEIGONG: "内功",
    WuxueType.QINGGONG: "轻功",
}


@dataclass
class Move:
    """招式定义.

    Attributes:
        key: 唯一标识
        name: 显示名
        wuxue_type: 武学类型
        mp_cost: 内力消耗
        ep_cost: 精力消耗
        cooldown: 冷却时间（秒）
        effect_script: 效果脚本（Python代码）
        counters: 克制的武学类型
        countered_by: 被克制的武学类型
    """

    key: str
    name: str
    wuxue_type: WuxueType
    mp_cost: int = 10
    ep_cost: int = 5
    cooldown: float = 0.0
    effect_script: str = ""
    counters: list[WuxueType] = field(default_factory=list)
    countered_by: list[WuxueType] = field(default_factory=list)


@dataclass
class MoveEffectResult:
    """招式效果结果."""

    damage: float = 0
    heal: float = 0
    effects: list[str] = field(default_factory=list)  # stun, poison, buff等
    messages: list[str] = field(default_factory=list)
    mp_cost: int = 0
    ep_cost: int = 0


class Kungfu:
    """武功定义.

    Attributes:
        key: 唯一标识
        name: 显示名
        menpai: 所属门派
        wuxue_type: 武学类型
        moves: 包含招式列表
        requirements: 学习条件
    """

    def __init__(
        self,
        key: str,
        name: str,
        menpai: str,
        wuxue_type: WuxueType,
        moves: list[Move] | None = None,
        requirements: dict | None = None,
        description: str = "",
    ):
        self.key = key
        self.name = name
        self.menpai = menpai
        self.wuxue_type = wuxue_type
        self.moves = moves or []
        self.requirements = requirements or {}
        self.description = description

    def get_move(self, move_key: str) -> Optional[Move]:
        """获取指定招式."""
        for move in self.moves:
            if move.key == move_key:
                return move
        return None

    def can_learn(self, character: "Character") -> tuple[bool, str]:
        """检查角色是否可以学习.

        Args:
            character: 角色

        Returns:
            (是否可以, 原因)
        """
        # 门派检查
        if self.menpai and character.menpai != self.menpai:
            return False, f"仅限{self.menpai}弟子学习"

        # 等级检查
        min_level = self.requirements.get("level", 1)
        if character.level < min_level:
            return False, f"等级不足（需要{min_level}级）"

        # 前置武功检查
        prereq = self.requirements.get("prerequisite")
        if prereq:
            learned = character.wuxue_learned
            if prereq not in learned:
                return False, f"需要先学习{prereq}"

        # 悟性检查
        min_wuxing = self.requirements.get("wuxing", 10)
        if character.wuxing < min_wuxing:
            return False, f"悟性不足（需要{min_wuxing}）"

        return True, ""


# 克制关系矩阵
# 行克制列
COUNTER_MATRIX: dict[WuxueType, list[WuxueType]] = {
    WuxueType.QUAN: [WuxueType.ZHANG, WuxueType.ZHI],
    WuxueType.ZHANG: [WuxueType.ZHI, WuxueType.JIAN],
    WuxueType.ZHI: [WuxueType.JIAN, WuxueType.DAO],
    WuxueType.JIAN: [WuxueType.DAO, WuxueType.GUN],
    WuxueType.DAO: [WuxueType.GUN, WuxueType.QUAN],
    WuxueType.GUN: [WuxueType.QUAN, WuxueType.ZHANG],
    WuxueType.NEIGONG: [WuxueType.QUAN, WuxueType.ZHANG],  # 内功克制外功拳掌
    WuxueType.QINGGONG: [WuxueType.GUN, WuxueType.DAO],  # 轻功克制重兵器
}

COUNTER_BONUS = 0.2  # 克制伤害加成
COUNTERED_PENALTY = -0.15  # 被克制伤害减成


def get_counter_modifier(
    attacker_type: WuxueType, defender_type: WuxueType
) -> float:
    """获取克制关系修正系数.

    Args:
        attacker_type: 攻击者武学类型
        defender_type: 防御者武学类型

    Returns:
        伤害修正系数
    """
    if defender_type in COUNTER_MATRIX.get(attacker_type, []):
        return 1 + COUNTER_BONUS

    # 检查是否被克制
    for wtype, counters in COUNTER_MATRIX.items():
        if attacker_type in counters and defender_type == wtype:
            return 1 + COUNTERED_PENALTY

    return 1.0


class CharacterWuxueMixin:
    """角色的武学管理."""

    @property
    def wuxue_learned(self) -> dict[str, dict]:
        """已学武功.

        Returns:
            {
                "kungfu_key": {
                    "level": 1,           # 层数/等级
                    "exp": 0,             # 熟练度经验
                    "moves": {            # 招式熟练度
                        "move_key": exp
                    }
                }
            }
        """
        return self.db.get("learned_wuxue", {})

    @wuxue_learned.setter
    def wuxue_learned(self, value: dict[str, dict]) -> None:
        self.db.set("learned_wuxue", value)

    async def wuxue_learn(self, kungfu: Kungfu) -> tuple[bool, str]:
        """学习武功.

        Args:
            kungfu: 武功对象

        Returns:
            (是否成功, 消息)
        """
        # 检查是否可以学习
        can_learn, reason = kungfu.can_learn(self)
        if not can_learn:
            return False, reason

        # 添加到已学武功
        learned = self.wuxue_learned
        learned[kungfu.key] = {
            "level": 1,
            "exp": 0,
            "moves": {move.key: 0 for move in kungfu.moves},
            "learned_at": "timestamp",
        }
        self.wuxue_learned = learned

        return True, f"你学会了「{kungfu.name}」！"

    def wuxue_has_learned(self, kungfu_key: str) -> bool:
        """是否已学某武功."""
        return kungfu_key in self.wuxue_learned

    def wuxue_get_level(self, kungfu_key: str) -> int:
        """获取武功层数."""
        wuxue = self.wuxue_learned.get(kungfu_key, {})
        return wuxue.get("level", 0)

    async def wuxue_practice(self, kungfu: Kungfu, move: Move) -> tuple[bool, str]:
        """练习招式，增加熟练度.

        Args:
            kungfu: 武功
            move: 招式

        Returns:
            (是否成功, 消息)
        """
        if not self.wuxue_has_learned(kungfu.key):
            return False, "你尚未学会这门武功"

        learned = self.wuxue_learned
        kungfu_data = learned[kungfu.key]

        # 增加熟练度
        current_exp = kungfu_data["moves"].get(move.key, 0)
        gain = self._wuxue_calc_practice_gain()
        kungfu_data["moves"][move.key] = current_exp + gain

        # 检查武功升级
        if self._wuxue_check_level_up(kungfu_data):
            kungfu_data["level"] += 1
            msg = f"「{kungfu.name}」提升至第{kungfu_data['level']}层！"
        else:
            msg = f"你练习了「{move.name}」，熟练度+{gain}"

        self.wuxue_learned = learned
        return True, msg

    def _wuxue_calc_practice_gain(self) -> int:
        """计算练习收益（受悟性影响）."""
        base = 10
        from_wuxing = self.wuxing // 3
        return base + from_wuxing

    def _wuxue_check_level_up(self, kungfu_data: dict) -> bool:
        """检查是否满足升级条件."""
        current_level = kungfu_data["level"]
        total_move_exp = sum(kungfu_data["moves"].values())

        # 需要总熟练度达到层数*100
        required = current_level * 100
        return total_move_exp >= required

    def wuxue_get_moves(self) -> list[tuple[Kungfu, Move]]:
        """获取所有可用招式."""
        from src.game.data.wuxue_registry import get_kungfu
        
        available: list[tuple[Kungfu, Move]] = []
        learned = self.wuxue_learned
        
        for kungfu_key, kungfu_data in learned.items():
            kungfu = get_kungfu(kungfu_key)
            if kungfu:
                # 获取该武功的所有招式
                for move_key in kungfu_data.get("moves", {}).keys():
                    move = kungfu.get_move(move_key)
                    if move:
                        available.append((kungfu, move))
        
        return available

    def wuxue_get_move_mastery(self, kungfu_key: str, move_key: str) -> int:
        """获取招式熟练度.

        Args:
            kungfu_key: 武功key
            move_key: 招式key

        Returns:
            熟练度
        """
        learned = self.wuxue_learned
        kungfu_data = learned.get(kungfu_key, {})
        moves = kungfu_data.get("moves", {})
        return moves.get(move_key, 0)

    def wuxue_get_total_mastery(self, kungfu_key: str) -> int:
        """获取武功总熟练度.

        Args:
            kungfu_key: 武功key

        Returns:
            总熟练度
        """
        learned = self.wuxue_learned
        kungfu_data = learned.get(kungfu_key, {})
        moves = kungfu_data.get("moves", {})
        return sum(moves.values())



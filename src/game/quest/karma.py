"""因果点系统."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class KarmaSystem:
    """因果点系统.

    记录玩家的道德选择和行为倾向，影响剧情走向和NPC态度。

    因果点类型：
    - good: 善良（帮助他人、行善）
    - evil: 邪恶（作恶、伤害无辜）
    - love: 多情（感情选择）
    - loyalty: 忠义（对门派/国家的忠诚）
    - wisdom: 智慧（解决谜题、策略选择）
    - courage: 勇气（面对危险的选择）
    """

    KARMA_TYPES = ["good", "evil", "love", "loyalty", "wisdom", "courage"]

    def __init__(self, character: Character):
        self.character = character

    def _get_karma(self) -> dict[str, int]:
        """获取原始因果点数据."""
        return self.character.db.get("karma", {})

    def _set_karma(self, karma: dict[str, int]) -> None:
        """保存因果点数据."""
        self.character.db.set("karma", karma)

    # ===== 基础操作 =====

    def add_karma(self, karma_type: str, points: int, reason: str = "") -> None:
        """添加因果点.

        Args:
            karma_type: 因果点类型
            points: 点数（可为负）
            reason: 原因/备注
        """
        if karma_type not in self.KARMA_TYPES:
            raise ValueError(f"未知的因果点类型: {karma_type}")

        karma = self._get_karma()
        old_value = karma.get(karma_type, 0)
        karma[karma_type] = old_value + points
        self._set_karma(karma)

        # 记录历史
        if reason:
            history = self.character.db.get("karma_history", [])
            if not isinstance(history, list):
                history = []
            history.append({
                "type": karma_type,
                "points": points,
                "reason": reason,
            })
            # 只保留最近100条
            self.character.db.set("karma_history", history[-100:])

    def get_karma(self, karma_type: str) -> int:
        """获取指定类型的因果点."""
        if karma_type not in self.KARMA_TYPES:
            return 0

        return self._get_karma().get(karma_type, 0)

    def get_karma_summary(self) -> dict[str, int]:
        """获取因果点汇总."""
        karma = self._get_karma()
        return {kt: karma.get(kt, 0) for kt in self.KARMA_TYPES}

    def get_karma_history(self) -> list[dict]:
        """获取因果点历史记录."""
        return self.character.db.get("karma_history", [])

    # ===== 条件检查 =====

    def check_requirement(self, requirement: dict[str, str]) -> bool:
        """检查因果点是否满足条件.

        Args:
            requirement: 条件字典，如 {"good": ">=10", "evil": "<=5"}

        Returns:
            是否满足所有条件
        """
        for karma_type, condition in requirement.items():
            if not self.check_single_requirement(karma_type, condition):
                return False
        return True

    def check_single_requirement(self, karma_type: str, condition: str) -> bool:
        """检查单个条件.

        Args:
            karma_type: 因果点类型
            condition: 条件字符串，如 ">=10", "<=5", "==0"

        Returns:
            是否满足
        """
        value = self.get_karma(karma_type)

        # 解析条件
        if ">=" in condition:
            threshold = int(condition.replace(">=", "").strip())
            return value >= threshold
        elif "<=" in condition:
            threshold = int(condition.replace("<=", "").strip())
            return value <= threshold
        elif ">" in condition:
            threshold = int(condition.replace(">", "").strip())
            return value > threshold
        elif "<" in condition:
            threshold = int(condition.replace("<", "").strip())
            return value < threshold
        elif "==" in condition:
            threshold = int(condition.replace("==", "").strip())
            return value == threshold
        else:
            # 默认 >=
            threshold = int(condition)
            return value >= threshold

    # ===== 派生属性 =====

    def get_alignment(self) -> str:
        """获取阵营倾向.

        Returns:
            阵营描述
        """
        good = self.get_karma("good")
        evil = self.get_karma("evil")

        diff = good - evil

        if diff >= 100:
            return "大侠"
        elif diff >= 50:
            return "善人"
        elif diff > -50:
            return "中立"
        elif diff > -100:
            return "恶人"
        else:
            return "魔头"

    def get_reputation_title(self) -> str:
        """获取声望称号."""
        loyalty = self.get_karma("loyalty")
        wisdom = self.get_karma("wisdom")
        courage = self.get_karma("courage")

        # 根据最高属性决定称号
        max_karma = max(loyalty, wisdom, courage)

        if max_karma < 10:
            return "无名小卒"

        if max_karma == loyalty:
            if loyalty >= 100:
                return "忠义之士"
            elif loyalty >= 50:
                return "可靠之人"
            else:
                return "有信之人"
        elif max_karma == wisdom:
            if wisdom >= 100:
                return "智者"
            elif wisdom >= 50:
                return "聪明人"
            else:
                return "有见识的人"
        else:  # courage
            if courage >= 100:
                return "勇者"
            elif courage >= 50:
                return "勇士"
            else:
                return "有勇气的人"

    def get_romance_style(self) -> str:
        """获取感情倾向."""
        love = self.get_karma("love")

        if love >= 100:
            return "情圣"
        elif love >= 50:
            return "多情种子"
        elif love > 0:
            return "有情之人"
        elif love == 0:
            return "无情"
        else:
            return "冷血"

    def get_summary_text(self) -> str:
        """获取因果点汇总文本（用于显示）."""
        lines = [
            f"阵营：{self.get_alignment()}",
            f"声望：{self.get_reputation_title()}",
            f"感情：{self.get_romance_style()}",
            "",
            "因果点：",
        ]

        for karma_type in self.KARMA_TYPES:
            value = self.get_karma(karma_type)
            name = {
                "good": "善良",
                "evil": "邪恶",
                "love": "多情",
                "loyalty": "忠义",
                "wisdom": "智慧",
                "courage": "勇气",
            }.get(karma_type, karma_type)
            lines.append(f"  {name}：{value}")

        return "\n".join(lines)


# 便捷函数

def add_karma(
    character: Character, karma_type: str, points: int, reason: str = ""
) -> None:
    """给角色添加因果点的便捷函数."""
    karma_sys = KarmaSystem(character)
    karma_sys.add_karma(karma_type, points, reason)


def check_karma_requirement(character: Character, requirement: dict[str, str]) -> bool:
    """检查角色因果点是否满足条件的便捷函数."""
    karma_sys = KarmaSystem(character)
    return karma_sys.check_requirement(requirement)

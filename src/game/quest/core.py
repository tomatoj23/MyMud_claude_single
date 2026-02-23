"""任务核心系统."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class QuestType(Enum):
    """任务类型."""

    MAIN = "main"  # 主线
    SIDE = "side"  # 支线
    DAILY = "daily"  # 日常
    MENPAI = "menpai"  # 门派


class QuestObjectiveType(Enum):
    """任务目标类型."""

    COLLECT = "collect"  # 收集物品
    KILL = "kill"  # 击杀NPC
    TALK = "talk"  # 对话
    EXPLORE = "explore"  # 探索地点
    CUSTOM = "custom"  # 自定义条件


@dataclass
class QuestObjective:
    """任务目标.

    Attributes:
        type: 目标类型
        target: 目标ID（物品key、NPC key、房间key等）
        count: 目标数量
        current: 当前进度（运行时）
        description: 目标描述
    """

    type: QuestObjectiveType
    target: str
    count: int = 1
    current: int = 0
    description: str = ""

    def is_complete(self) -> bool:
        """检查是否已完成."""
        return self.current >= self.count

    def update(self, progress: int) -> bool:
        """更新进度.

        Args:
            progress: 进度增量

        Returns:
            是否刚好完成
        """
        was_complete = self.is_complete()
        self.current = self.current + progress  # 允许超过count
        return not was_complete and self.is_complete()


@dataclass
class Quest:
    """任务定义.

    Attributes:
        key: 唯一标识
        name: 任务名
        description: 任务描述
        quest_type: 任务类型
        objectives: 任务目标列表
        rewards: 奖励配置
        prerequisites: 前置条件
        next_quest: 后续任务key
        time_limit: 时间限制（秒，None表示无限制）
    """

    key: str
    name: str
    description: str
    quest_type: QuestType
    objectives: list[QuestObjective] = field(default_factory=list)
    rewards: dict = field(default_factory=dict)
    prerequisites: dict = field(default_factory=dict)
    next_quest: str | None = None
    time_limit: int | None = None

    def can_accept(self, character: Character) -> tuple[bool, str]:
        """检查角色是否可以接受任务.

        Args:
            character: 角色

        Returns:
            (是否可以, 原因)
        """
        prereqs = self.prerequisites

        # 等级要求
        if "level" in prereqs:
            if character.level < prereqs["level"]:
                return False, f"需要等级{prereqs['level']}"

        # 门派要求
        if "menpai" in prereqs:
            if character.menpai != prereqs["menpai"]:
                return False, f"仅限{prereqs['menpai']}弟子"

        # 前置任务
        if "quest_completed" in prereqs:
            completed = character.db.get("completed_quests", [])
            if prereqs["quest_completed"] not in completed:
                return False, "需要先完成前置任务"

        # 因果点要求
        if "karma" in prereqs:
            from .karma import KarmaSystem

            karma_sys = KarmaSystem(character)
            for karma_type, condition in prereqs["karma"].items():
                if not karma_sys.check_single_requirement(karma_type, condition):
                    return False, f"因果点不满足条件"

        return True, ""


class CharacterQuestMixin:
    """角色的任务管理 Mixin.

    提供任务相关的所有功能：
    - 接受/放弃任务
    - 更新任务进度
    - 完成任务并领取奖励
    """

    # ===== 数据访问 =====

    @property
    def active_quests(self) -> dict[str, dict]:
        """进行中任务.

        Returns:
            {quest_key: progress_data}
        """
        return self.db.get("active_quests", {})

    @active_quests.setter
    def active_quests(self, value: dict[str, dict]) -> None:
        self.db.set("active_quests", value)

    @property
    def completed_quests(self) -> list[str]:
        """已完成任务key列表."""
        return self.db.get("completed_quests", [])

    @completed_quests.setter
    def completed_quests(self, value: list[str]) -> None:
        self.db.set("completed_quests", value)

    # ===== 任务操作 =====

    async def accept_quest(self, quest: Quest) -> tuple[bool, str]:
        """接受任务.

        Args:
            quest: 任务对象

        Returns:
            (是否成功, 消息)
        """
        # 检查前置条件
        can_accept, reason = quest.can_accept(self)
        if not can_accept:
            return False, reason

        # 检查是否已接受
        if quest.key in self.active_quests:
            return False, "你已接受该任务"

        # 检查是否已完成（非重复任务）
        if quest.key in self.completed_quests and quest.quest_type != QuestType.DAILY:
            return False, "你已完成该任务"

        # 创建任务进度数据
        from datetime import datetime

        active = self.active_quests
        active[quest.key] = {
            "accepted_at": datetime.now().isoformat(),
            "objectives": [
                {
                    "type": obj.type.value,
                    "target": obj.target,
                    "count": obj.count,
                    "current": 0,
                }
                for obj in quest.objectives
            ],
            "time_limit": quest.time_limit,
        }
        self.active_quests = active

        return True, f"接受任务：{quest.name}"

    async def abandon_quest(self, quest_key: str) -> tuple[bool, str]:
        """放弃任务.

        Args:
            quest_key: 任务key

        Returns:
            (是否成功, 消息)
        """
        active = self.active_quests

        if quest_key not in active:
            return False, "你没有进行该任务"

        del active[quest_key]
        self.active_quests = active

        return True, "已放弃任务"

    async def update_objective(
        self, quest_key: str, objective_idx: int, progress: int = 1
    ) -> tuple[bool, str]:
        """更新任务进度.

        Args:
            quest_key: 任务key
            objective_idx: 目标索引
            progress: 进度增量

        Returns:
            (是否完成该目标, 消息)
        """
        active = self.active_quests

        if quest_key not in active:
            return False, ""

        quest_data = active[quest_key]
        objectives = quest_data.get("objectives", [])

        if objective_idx >= len(objectives):
            return False, ""

        obj_data = objectives[objective_idx]

        # 检查是否已完成
        if obj_data["current"] >= obj_data["count"]:
            return False, ""

        # 更新进度
        old_current = obj_data["current"]
        obj_data["current"] = min(obj_data["count"], old_current + progress)

        self.active_quests = active

        # 返回是否刚好完成
        just_completed = old_current < obj_data["count"] and obj_data["current"] >= obj_data["count"]

        if just_completed:
            return True, f"任务目标完成！"
        return False, f"进度更新：{obj_data['current']}/{obj_data['count']}"

    async def complete_quest(self, quest_key: str, quest_def: Quest | None = None) -> tuple[bool, str]:
        """完成任务.

        Args:
            quest_key: 任务key
            quest_def: 任务定义（用于发放奖励）

        Returns:
            (是否成功, 消息)
        """
        active = self.active_quests

        if quest_key not in active:
            return False, "你没有进行该任务"

        quest_data = active[quest_key]
        objectives = quest_data.get("objectives", [])

        # 检查所有目标是否完成
        for obj in objectives:
            if obj["current"] < obj["count"]:
                return False, "任务目标尚未完成"

        # 发放奖励
        rewards_msg = ""
        if quest_def:
            rewards_msg = await self._give_rewards(quest_def.rewards)

        # 移动到已完成
        del active[quest_key]
        self.active_quests = active

        completed = self.completed_quests
        if quest_key not in completed:
            completed.append(quest_key)
            self.completed_quests = completed

        return True, f"任务完成！{rewards_msg}"

    async def _give_rewards(self, rewards: dict) -> str:
        """发放任务奖励.

        Args:
            rewards: 奖励配置

        Returns:
            奖励描述
        """
        msgs = []

        # 经验奖励
        if "exp" in rewards:
            exp = rewards["exp"]
            if hasattr(self, "add_exp"):
                self.add_exp(exp)
            msgs.append(f"经验 +{exp}")

        # 潜能奖励
        if "potential" in rewards:
            pot = rewards["potential"]
            current = self.db.get("potential", 0)
            self.db.set("potential", current + pot)
            msgs.append(f"潜能 +{pot}")

        # 银两奖励
        if "silver" in rewards:
            silver = rewards["silver"]
            current = self.db.get("silver", 0)
            self.db.set("silver", current + silver)
            msgs.append(f"银两 +{silver}")

        # 物品奖励
        if "items" in rewards:
            # TODO: 实现物品发放
            msgs.append("获得物品")

        # 武学奖励
        if "wuxue" in rewards:
            # TODO: 实现武学奖励
            msgs.append("领悟武学")

        # 声望奖励
        if "reputation" in rewards:
            rep = rewards["reputation"]
            current = self.db.get("reputation", 0)
            self.db.set("reputation", current + rep)
            msgs.append(f"声望 +{rep}")

        return " ".join(msgs) if msgs else ""

    # ===== 查询方法 =====

    def get_quest_progress(self, quest_key: str) -> dict | None:
        """获取任务进度."""
        return self.active_quests.get(quest_key)

    def is_quest_active(self, quest_key: str) -> bool:
        """检查任务是否进行中."""
        return quest_key in self.active_quests

    def is_quest_completed(self, quest_key: str) -> bool:
        """检查任务是否已完成."""
        return quest_key in self.completed_quests

    def get_active_quest_list(self) -> list[dict]:
        """获取活跃任务列表（用于显示）."""
        return [
            {"key": k, **v}
            for k, v in self.active_quests.items()
        ]

    def get_objective_progress(self, quest_key: str, objective_idx: int) -> tuple[int, int]:
        """获取指定目标的进度.

        Returns:
            (当前进度, 目标数量)
        """
        quest_data = self.active_quests.get(quest_key)
        if not quest_data:
            return (0, 0)

        objectives = quest_data.get("objectives", [])
        if objective_idx >= len(objectives):
            return (0, 0)

        obj = objectives[objective_idx]
        return (obj["current"], obj["count"])

    # ===== 便捷更新方法 =====

    async def on_kill_npc(self, npc_key: str) -> list[str]:
        """击杀NPC时调用，更新相关任务进度.

        Returns:
            进度更新消息列表
        """
        messages = []

        for quest_key, quest_data in self.active_quests.items():
            objectives = quest_data.get("objectives", [])
            for idx, obj in enumerate(objectives):
                if obj["type"] == QuestObjectiveType.KILL.value and obj["target"] == npc_key:
                    completed, msg = await self.update_objective(quest_key, idx, 1)
                    if msg:
                        messages.append(f"[{quest_key}] {msg}")

        return messages

    async def on_collect_item(self, item_key: str, count: int = 1) -> list[str]:
        """收集物品时调用，更新相关任务进度."""
        messages = []

        for quest_key, quest_data in self.active_quests.items():
            objectives = quest_data.get("objectives", [])
            for idx, obj in enumerate(objectives):
                if obj["type"] == QuestObjectiveType.COLLECT.value and obj["target"] == item_key:
                    completed, msg = await self.update_objective(quest_key, idx, count)
                    if msg:
                        messages.append(f"[{quest_key}] {msg}")

        return messages

    async def on_talk_to_npc(self, npc_key: str) -> list[str]:
        """与NPC对话时调用，更新相关任务进度."""
        messages = []

        for quest_key, quest_data in self.active_quests.items():
            objectives = quest_data.get("objectives", [])
            for idx, obj in enumerate(objectives):
                if obj["type"] == QuestObjectiveType.TALK.value and obj["target"] == npc_key:
                    completed, msg = await self.update_objective(quest_key, idx, 1)
                    if msg:
                        messages.append(f"[{quest_key}] {msg}")

        return messages

    async def on_explore_room(self, room_key: str) -> list[str]:
        """探索房间时调用，更新相关任务进度."""
        messages = []

        for quest_key, quest_data in self.active_quests.items():
            objectives = quest_data.get("objectives", [])
            for idx, obj in enumerate(objectives):
                if obj["type"] == QuestObjectiveType.EXPLORE.value and obj["target"] == room_key:
                    completed, msg = await self.update_objective(quest_key, idx, 1)
                    if msg:
                        messages.append(f"[{quest_key}] {msg}")

        return messages

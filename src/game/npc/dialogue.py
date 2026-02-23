"""NPC对话系统."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character
    from .core import NPC


@dataclass
class Response:
    """对话回应选项.

    Attributes:
        text: 选项文本
        next_node: 下一个对话节点ID
        conditions: 显示条件（如好感度要求）
        effects: 选择后的效果（如好感度变化）
    """

    text: str
    next_node: str | None = None
    conditions: dict = field(default_factory=dict)
    effects: dict = field(default_factory=dict)


@dataclass
class DialogueNode:
    """对话节点.

    Attributes:
        text: NPC说的话
        responses: 玩家回应选项列表
        conditions: 显示条件
        effects: 显示后的效果
        on_enter: 进入节点时的回调
    """

    text: str
    responses: list[Response] = field(default_factory=list)
    conditions: dict = field(default_factory=dict)
    effects: dict = field(default_factory=dict)
    on_enter: Callable[[Character, NPC], None] | None = None


class DialogueSystem:
    """对话系统.

    管理所有NPC的对话配置，处理对话流程。

    Example:
        # 注册对话
        dialogue_sys = DialogueSystem()
        dialogue_sys.register_dialogue("wang_daye", "default", DialogueNode(
            text="客官，需要点什么？",
            responses=[
                Response("我想买点东西", next_node="shop"),
                Response("随便看看", next_node=None),
            ]
        ))

        # 开始对话
        node = dialogue_sys.start_dialogue(player, npc)
        # 选择回应
        next_node = dialogue_sys.select_response(player, npc, node, 0)
    """

    def __init__(self):
        # {npc_key: {node_id: DialogueNode}}
        self.dialogues: dict[str, dict[str, DialogueNode]] = {}

    def register_dialogue(
        self, npc_key: str, node_id: str, node: DialogueNode
    ) -> None:
        """注册对话节点.

        Args:
            npc_key: NPC标识
            node_id: 节点ID
            node: 对话节点
        """
        if npc_key not in self.dialogues:
            self.dialogues[npc_key] = {}
        self.dialogues[npc_key][node_id] = node

    def register_dialogue_tree(
        self, npc_key: str, nodes: dict[str, DialogueNode]
    ) -> None:
        """批量注册对话树.

        Args:
            npc_key: NPC标识
            nodes: 节点字典 {node_id: DialogueNode}
        """
        self.dialogues[npc_key] = nodes

    def get_node(self, npc_key: str, node_id: str) -> DialogueNode | None:
        """获取对话节点.

        Args:
            npc_key: NPC标识
            node_id: 节点ID

        Returns:
            对话节点，不存在返回None
        """
        return self.dialogues.get(npc_key, {}).get(node_id)

    async def start_dialogue(
        self, character: Character, npc: NPC
    ) -> DialogueNode | None:
        """开始对话.

        根据好感度选择起始节点。

        Args:
            character: 玩家角色
            npc: NPC对象

        Returns:
            起始对话节点
        """
        npc_key = npc.get_dialogue_key()
        npc_dialogues = self.dialogues.get(npc_key, {})

        if not npc_dialogues:
            return None

        # 获取好感度
        favor = character.npc_relations.get_favor(npc_key)

        # 根据好感度选择起始节点
        if favor <= -50 and "hostile" in npc_dialogues:
            start_node_id = "hostile"
        elif favor >= 100 and "friendly" in npc_dialogues:
            start_node_id = "friendly"
        elif favor >= 50 and "know" in npc_dialogues:
            start_node_id = "know"
        elif "default" in npc_dialogues:
            start_node_id = "default"
        else:
            # 使用第一个可用节点
            start_node_id = next(iter(npc_dialogues.keys()))

        node = npc_dialogues.get(start_node_id)

        # 检查节点显示条件
        if node and self._check_conditions(character, npc, node.conditions):
            # 执行进入效果
            await self._apply_effects(character, npc, node.effects)
            if node.on_enter:
                result = node.on_enter(character, npc)
                import asyncio
                import inspect
                if result is not None and asyncio.iscoroutine(result):
                    await result
            return node

        return None

    def get_available_responses(
        self, character: Character, npc: NPC, node: DialogueNode
    ) -> list[tuple[int, Response]]:
        """获取可用的回应选项.

        Args:
            character: 玩家角色
            npc: NPC对象
            node: 当前对话节点

        Returns:
            (索引, 回应)列表
        """
        available = []

        for idx, response in enumerate(node.responses):
            if self._check_conditions(character, npc, response.conditions):
                available.append((idx, response))

        return available

    async def select_response(
        self,
        character: Character,
        npc: NPC,
        current_node: DialogueNode,
        response_idx: int,
    ) -> DialogueNode | None:
        """选择回应.

        Args:
            character: 玩家角色
            npc: NPC对象
            current_node: 当前对话节点
            response_idx: 回应选项索引

        Returns:
            下一个对话节点，对话结束返回None
        """
        if response_idx >= len(current_node.responses):
            return None

        response = current_node.responses[response_idx]

        # 应用效果
        await self._apply_effects(character, npc, response.effects)

        # 获取下一个节点
        if not response.next_node:
            return None

        npc_key = npc.get_dialogue_key()
        next_node = self.get_node(npc_key, response.next_node)

        if next_node:
            # 检查节点条件
            if not self._check_conditions(character, npc, next_node.conditions):
                return None

            # 应用节点效果
            await self._apply_effects(character, npc, next_node.effects)
            if next_node.on_enter:
                result = next_node.on_enter(character, npc)
                import asyncio
                if result is not None and asyncio.iscoroutine(result):
                    await result

        return next_node

    def _check_conditions(
        self, character: Character, npc: NPC, conditions: dict
    ) -> bool:
        """检查条件是否满足.

        Args:
            character: 玩家角色
            npc: NPC对象
            conditions: 条件字典

        Returns:
            是否满足
        """
        if not conditions:
            return True

        # 好感度条件
        if "min_favor" in conditions:
            favor = character.npc_relations.get_favor(npc.key)
            if favor < conditions["min_favor"]:
                return False

        if "max_favor" in conditions:
            favor = character.npc_relations.get_favor(npc.key)
            if favor > conditions["max_favor"]:
                return False

        # 等级条件
        if "min_level" in conditions:
            if character.level < conditions["min_level"]:
                return False

        # 门派条件
        if "menpai" in conditions:
            if character.menpai != conditions["menpai"]:
                return False

        # 任务条件
        if "quest_active" in conditions:
            if not character.is_quest_active(conditions["quest_active"]):
                return False

        if "quest_completed" in conditions:
            if not character.is_quest_completed(conditions["quest_completed"]):
                return False

        # 物品条件
        if "has_item" in conditions:
            # TODO: 检查背包
            pass

        # 因果点条件
        if "karma" in conditions:
            from src.game.quest.karma import KarmaSystem

            karma_sys = KarmaSystem(character)
            for karma_type, condition in conditions["karma"].items():
                if not karma_sys.check_single_requirement(karma_type, condition):
                    return False

        return True

    async def _apply_effects(
        self, character: Character, npc: NPC, effects: dict
    ) -> None:
        """应用效果.

        Args:
            character: 玩家角色
            npc: NPC对象
            effects: 效果字典
        """
        if not effects:
            return

        # 好感度变化
        if "favor_delta" in effects:
            delta = effects["favor_delta"]
            reason = effects.get("favor_reason", "")
            character.npc_relations.modify_favor(npc.key, delta, reason)

        # 给予物品
        if "give_item" in effects:
            item_key = effects["give_item"]
            count = effects.get("item_count", 1)
            # TODO: 给予物品
            pass

        # 给予银两
        if "give_silver" in effects:
            amount = effects["give_silver"]
            current = character.db.get("silver", 0)
            character.db.set("silver", current + amount)

        # 给予经验
        if "give_exp" in effects:
            exp = effects["give_exp"]
            if hasattr(character, "add_exp"):
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(character.add_exp):
                    await character.add_exp(exp)
                else:
                    character.add_exp(exp)

        # 解锁任务
        if "unlock_quest" in effects:
            quest_key = effects["unlock_quest"]
            # TODO: 解锁任务
            pass

        # 因果点变化
        if "karma" in effects:
            from src.game.quest.karma import KarmaSystem

            karma_sys = KarmaSystem(character)
            for karma_type, points in effects["karma"].items():
                karma_sys.add_karma(karma_type, points)

        # 记录选择
        if "record_choice" in effects:
            choice_id = effects["record_choice"]
            choice_value = effects.get("choice_value", "")
            # TODO: 记录到世界状态
            pass

    def format_dialogue(
        self, character: Character, npc: NPC, node: DialogueNode
    ) -> dict:
        """格式化对话内容（用于显示）.

        Args:
            character: 玩家角色
            npc: NPC对象
            node: 对话节点

        Returns:
            格式化后的对话数据
        """
        available_responses = self.get_available_responses(character, npc, node)

        return {
            "npc_name": npc.name,
            "text": node.text,
            "responses": [
                {
                    "index": idx,
                    "text": response.text,
                }
                for idx, response in available_responses
            ],
        }


# ===== 便捷函数 =====

def create_simple_dialogue(
    npc_text: str, response_texts: list[str]
) -> DialogueNode:
    """创建简单对话节点.

    Args:
        npc_text: NPC说的话
        response_texts: 玩家回应列表

    Returns:
        对话节点
    """
    responses = [Response(text=text) for text in response_texts]
    return DialogueNode(text=npc_text, responses=responses)


def create_trade_dialogue(npc_name: str) -> dict[str, DialogueNode]:
    """创建商人对话树.

    Args:
        npc_name: NPC名字

    Returns:
        对话节点字典
    """
    return {
        "default": DialogueNode(
            text=f"客官，欢迎光临小店。需要点什么？",
            responses=[
                Response("我要买东西", next_node="shop"),
                Response("我想卖东西", next_node="sell"),
                Response("随便看看", next_node=None),
            ],
        ),
        "shop": DialogueNode(
            text="请看，这些都是本店的商品。",
            responses=[
                Response("返回", next_node="default"),
                Response("离开", next_node=None),
            ],
        ),
        "sell": DialogueNode(
            text="客官要卖什么？让我看看。",
            responses=[
                Response("返回", next_node="default"),
                Response("离开", next_node=None),
            ],
        ),
    }


def create_quest_dialogue(npc_name: str, quest_name: str) -> dict[str, DialogueNode]:
    """创建任务NPC对话树.

    Args:
        npc_name: NPC名字
        quest_name: 任务名字

    Returns:
        对话节点字典
    """
    return {
        "default": DialogueNode(
            text=f"这位少侠，老夫有一事相求。",
            responses=[
                Response("请讲", next_node="quest_desc"),
                Response("没空", next_node=None),
            ],
        ),
        "quest_desc": DialogueNode(
            text=f"{quest_name}，不知少侠可愿意帮忙？",
            responses=[
                Response("乐意效劳", next_node="accept", effects={"unlock_quest": "quest_key"}),
                Response("考虑一下", next_node=None),
            ],
        ),
        "accept": DialogueNode(
            text="太好了！多谢少侠！",
            responses=[
                Response("客气了", next_node=None),
            ],
        ),
    }

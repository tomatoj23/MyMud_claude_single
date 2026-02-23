"""世界状态管理."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine
    from src.game.typeclasses.character import Character


class WorldStateManager:
    """世界状态管理.

    管理全局的世界状态，如：
    - 任务相关的事件标志
    - 玩家的剧情选择
    - 世界事件状态
    """

    def __init__(self, engine: GameEngine | None = None):
        self.engine = engine
        self._states: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取世界状态.

        Args:
            key: 状态键
            default: 默认值

        Returns:
            状态值
        """
        return self._states.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置世界状态.

        Args:
            key: 状态键
            value: 状态值
        """
        self._states[key] = value

    def has(self, key: str) -> bool:
        """检查状态是否存在."""
        return key in self._states

    def delete(self, key: str) -> bool:
        """删除状态.

        Returns:
            是否成功删除
        """
        if key in self._states:
            del self._states[key]
            return True
        return False

    def increment(self, key: str, amount: int = 1) -> int:
        """增加数值状态.

        Args:
            key: 状态键
            amount: 增量

        Returns:
            增加后的值
        """
        current = self._states.get(key, 0)
        if not isinstance(current, (int, float)):
            current = 0
        new_value = current + amount
        self._states[key] = new_value
        return new_value

    def toggle(self, key: str) -> bool:
        """切换布尔状态.

        Returns:
            切换后的值
        """
        current = self._states.get(key, False)
        new_value = not bool(current)
        self._states[key] = new_value
        return new_value

    # ===== 玩家选择记录 =====

    def on_player_choice(
        self, character: Character, choice_id: str, choice: str
    ) -> None:
        """记录玩家选择.

        Args:
            character: 玩家角色
            choice_id: 选择标识
            choice: 选择内容
        """
        key = f"choice_{character.id}_{choice_id}"
        self._states[key] = {
            "choice": choice,
            "character_id": character.id,
        }

    def get_player_choice(self, character: Character, choice_id: str) -> str | None:
        """获取玩家的选择.

        Args:
            character: 玩家角色
            choice_id: 选择标识

        Returns:
            选择内容，未选择返回None
        """
        key = f"choice_{character.id}_{choice_id}"
        data = self._states.get(key)
        if data and isinstance(data, dict):
            return data.get("choice")
        return None

    def has_made_choice(self, character: Character, choice_id: str) -> bool:
        """检查玩家是否已做出选择."""
        key = f"choice_{character.id}_{choice_id}"
        return key in self._states

    # ===== 任务事件标志 =====

    def set_quest_flag(self, quest_key: str, flag: str, value: Any = True) -> None:
        """设置任务标志.

        Args:
            quest_key: 任务key
            flag: 标志名
            value: 标志值
        """
        key = f"quest_{quest_key}_{flag}"
        self._states[key] = value

    def get_quest_flag(self, quest_key: str, flag: str, default: Any = None) -> Any:
        """获取任务标志."""
        key = f"quest_{quest_key}_{flag}"
        return self._states.get(key, default)

    def has_quest_flag(self, quest_key: str, flag: str) -> bool:
        """检查任务标志是否存在."""
        key = f"quest_{quest_key}_{flag}"
        return key in self._states

    # ===== 全局事件 =====

    def set_global_event(self, event_key: str, active: bool = True) -> None:
        """设置全局事件状态.

        Args:
            event_key: 事件标识
            active: 是否激活
        """
        key = f"event_{event_key}"
        self._states[key] = active

    def is_event_active(self, event_key: str) -> bool:
        """检查事件是否激活."""
        key = f"event_{event_key}"
        return bool(self._states.get(key, False))

    def trigger_event(self, event_key: str) -> None:
        """触发一次性事件."""
        key = f"triggered_{event_key}"
        self._states[key] = True

    def has_event_triggered(self, event_key: str) -> bool:
        """检查事件是否已触发过."""
        key = f"triggered_{event_key}"
        return key in self._states

    # ===== 批量操作 =====

    def get_all_states(self) -> dict[str, Any]:
        """获取所有状态."""
        return self._states.copy()

    def clear(self) -> None:
        """清除所有状态."""
        self._states.clear()

    def clear_player_states(self, character: Character) -> None:
        """清除指定玩家的所有状态."""
        prefix = f"choice_{character.id}_"
        keys_to_remove = [k for k in self._states.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._states[key]

    def export_states(self, prefix: str = "") -> dict[str, Any]:
        """导出指定前缀的状态.

        Args:
            prefix: 状态键前缀

        Returns:
            状态字典
        """
        if prefix:
            return {k: v for k, v in self._states.items() if k.startswith(prefix)}
        return self._states.copy()

    def import_states(self, states: dict[str, Any], overwrite: bool = True) -> None:
        """导入状态.

        Args:
            states: 状态字典
            overwrite: 是否覆盖已有状态
        """
        for key, value in states.items():
            if overwrite or key not in self._states:
                self._states[key] = value

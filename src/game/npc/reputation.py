"""NPC好感度系统."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class NPCRelationship:
    """NPC关系管理.

    管理玩家与各NPC之间的好感度和关系历史。

    关系等级：
    - 仇敌（-100以下）
    - 冷淡（-50~-100）
    - 陌生（-50~50）
    - 友善（50~100）
    - 尊敬（100~200）
    - 至交（200以上）
    """

    RELATIONSHIP_LEVELS = [
        (-100, "仇敌"),
        (-50, "冷淡"),
        (0, "陌生"),
        (50, "友善"),
        (100, "尊敬"),
        (200, "至交"),
    ]

    # 关系变化阈值
    HOSTILE_THRESHOLD = -50
    FRIENDLY_THRESHOLD = 50

    def __init__(self, character: Character):
        self.character = character

    def _get_relations(self) -> dict:
        """获取原始关系数据."""
        return self.character.db.get("npc_relations", {})

    def _set_relations(self, relations: dict) -> None:
        """保存关系数据."""
        self.character.db.set("npc_relations", relations)

    # ===== 基础操作 =====

    def get_favor(self, npc_id: str) -> int:
        """获取对特定NPC的好感度.

        Args:
            npc_id: NPC标识

        Returns:
            好感度数值
        """
        relations = self._get_relations()
        return relations.get(npc_id, {}).get("favor", 0)

    def modify_favor(self, npc_id: str, delta: int, reason: str = "") -> int:
        """修改好感度.

        Args:
            npc_id: NPC标识
            delta: 变化值（可为负）
            reason: 原因/备注

        Returns:
            修改后的好感度
        """
        relations = self._get_relations()

        if npc_id not in relations:
            relations[npc_id] = {"favor": 0, "history": []}

        # 更新好感度
        old_favor = relations[npc_id]["favor"]
        new_favor = old_favor + delta
        relations[npc_id]["favor"] = new_favor

        # 记录历史
        if reason or delta != 0:
            history = relations[npc_id].get("history", [])
            history.append({
                "delta": delta,
                "reason": reason,
                "old_favor": old_favor,
                "new_favor": new_favor,
            })
            # 只保留最近20条
            relations[npc_id]["history"] = history[-20:]

        self._set_relations(relations)
        return new_favor

    def set_favor(self, npc_id: str, value: int) -> None:
        """直接设置好感度（用于初始化）."""
        relations = self._get_relations()

        if npc_id not in relations:
            relations[npc_id] = {"favor": 0, "history": []}

        relations[npc_id]["favor"] = value
        self._set_relations(relations)

    def get_relationship_level(self, npc_id: str) -> str:
        """获取关系等级名称.

        Args:
            npc_id: NPC标识

        Returns:
            关系等级描述
        """
        favor = self.get_favor(npc_id)

        # 区间定义（根据类注释）：
        # (-∞, -100): 仇敌
        # [-100, -50): 冷淡  
        # [-50, 50): 陌生（测试期望-50~50为陌生）
        # [50, 100): 友善
        # [100, 200): 尊敬
        # [200, +∞): 至交
        if favor < -100:
            return "仇敌"
        elif favor < -50:
            return "冷淡"
        elif favor < 50:
            return "陌生"
        elif favor < 100:
            return "友善"
        elif favor < 200:
            return "尊敬"
        else:
            return "至交"

    def get_favor_status(self, npc_id: str) -> dict:
        """获取完整的好感度状态.

        Returns:
            状态字典
        """
        favor = self.get_favor(npc_id)
        return {
            "npc_id": npc_id,
            "favor": favor,
            "level": self.get_relationship_level(npc_id),
            "is_hostile": favor <= self.HOSTILE_THRESHOLD,
            "is_friendly": favor >= self.FRIENDLY_THRESHOLD,
        }

    # ===== 关系判断 =====

    def is_hostile(self, npc_id: str) -> bool:
        """是否为敌对关系."""
        return self.get_favor(npc_id) <= self.HOSTILE_THRESHOLD

    def is_friendly(self, npc_id: str) -> bool:
        """是否为友好关系."""
        return self.get_favor(npc_id) >= self.FRIENDLY_THRESHOLD

    def is_stranger(self, npc_id: str) -> bool:
        """是否为陌生关系."""
        favor = self.get_favor(npc_id)
        return self.HOSTILE_THRESHOLD < favor < self.FRIENDLY_THRESHOLD

    def can_trade(self, npc_id: str) -> bool:
        """是否可以交易."""
        # 非敌对即可交易
        return not self.is_hostile(npc_id)

    def can_learn(self, npc_id: str) -> bool:
        """是否可以学习武功."""
        # 友好关系才能学习
        return self.is_friendly(npc_id)

    def will_help(self, npc_id: str) -> bool:
        """是否会帮助玩家."""
        # 尊敬以上才会主动帮助
        return self.get_favor(npc_id) >= 100

    # ===== 历史记录 =====

    def get_history(self, npc_id: str) -> list[dict]:
        """获取与NPC的互动历史.

        Returns:
            历史记录列表
        """
        relations = self._get_relations()
        return relations.get(npc_id, {}).get("history", [])

    def get_all_relations(self) -> list[dict]:
        """获取所有NPC关系.

        Returns:
            关系列表
        """
        relations = self._get_relations()
        return [
            {
                "npc_id": npc_id,
                "favor": data.get("favor", 0),
                "level": self.get_relationship_level(npc_id),
            }
            for npc_id, data in relations.items()
        ]

    def get_friendly_npcs(self) -> list[str]:
        """获取友好关系的NPC列表.

        Returns:
            NPC ID列表
        """
        return [
            npc_id
            for npc_id in self._get_relations().keys()
            if self.is_friendly(npc_id)
        ]

    def get_hostile_npcs(self) -> list[str]:
        """获取敌对关系的NPC列表.

        Returns:
            NPC ID列表
        """
        return [
            npc_id
            for npc_id in self._get_relations().keys()
            if self.is_hostile(npc_id)
        ]

    # ===== 批量操作 =====

    def clear_history(self, npc_id: str) -> None:
        """清除与某NPC的历史记录."""
        relations = self._get_relations()
        if npc_id in relations:
            relations[npc_id]["history"] = []
            self._set_relations(relations)

    def reset_favor(self, npc_id: str) -> None:
        """重置与某NPC的好感度."""
        self.set_favor(npc_id, 0)

    def clear_all_relations(self) -> None:
        """清除所有关系数据."""
        self._set_relations({})

    # ===== 派系关系（TD-009） =====

    def get_faction_favor(self, faction_id: str) -> int:
        """获取派系好感度.
        
        Args:
            faction_id: 派系ID（如"少林", "武当"）
            
        Returns:
            好感度值（-10000到10000，0为中立）
        """
        relations = self._get_relations()
        faction_relations = relations.get("factions", {})
        return faction_relations.get(faction_id, 0)

    def modify_faction_favor(self, faction_id: str, delta: int) -> int:
        """修改派系好感度.
        
        Args:
            faction_id: 派系ID
            delta: 变化值（正数为增加好感，负数为减少）
            
        Returns:
            新的好感度值
        """
        relations = self._get_relations()
        
        # 确保factions字典存在
        if "factions" not in relations:
            relations["factions"] = {}
        
        # 计算新值（限制范围）
        current = relations["factions"].get(faction_id, 0)
        new_value = max(-10000, min(10000, current + delta))
        
        relations["factions"][faction_id] = new_value
        self._set_relations(relations)
        
        return new_value
    
    def get_faction_standings(self) -> dict[str, int]:
        """获取所有派系关系.
        
        Returns:
            派系关系字典 {派系ID: 好感度}
        """
        relations = self._get_relations()
        return relations.get("factions", {}).copy()
    
    def get_faction_title(self, faction_id: str) -> str:
        """获取在派系中的称号.
        
        Args:
            faction_id: 派系ID
            
        Returns:
            称号字符串
        """
        favor = self.get_faction_favor(faction_id)
        
        # 根据好感度返回称号
        if favor >= 5000:
            return "崇敬"
        elif favor >= 2000:
            return "尊敬"
        elif favor >= 500:
            return "友好"
        elif favor >= -500:
            return "中立"
        elif favor >= -2000:
            return "冷淡"
        elif favor >= -5000:
            return "敌对"
        else:
            return "仇恨"
    
    def is_faction_hostile(self, faction_id: str) -> bool:
        """检查派系是否敌对.
        
        Args:
            faction_id: 派系ID
            
        Returns:
            是否敌对（好感度<=-2000）
        """
        return self.get_faction_favor(faction_id) <= -2000
    
    def is_faction_friendly(self, faction_id: str) -> bool:
        """检查派系是否友好.
        
        Args:
            faction_id: 派系ID
            
        Returns:
            是否友好（好感度>=500）
        """
        return self.get_faction_favor(faction_id) >= 500
    
    def reset_faction_favor(self, faction_id: str) -> None:
        """重置派系好感度为0.
        
        Args:
            faction_id: 派系ID
        """
        self.modify_faction_favor(faction_id, -self.get_faction_favor(faction_id))

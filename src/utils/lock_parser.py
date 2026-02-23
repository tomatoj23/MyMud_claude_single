"""出口锁解析器.

实现锁字符串语法解析和条件检查.

锁字符串语法:
    has_item:key:quantity       - 需要物品
    has_skill:key:level         - 需要技能等级
    attr:name:op:value          - 属性比较 (op: ==, !=, <, <=, >, >=)
    time:start:end              - 时间限制 (HH:MM格式)
    quest:key:status            - 任务状态 (active/completed/failed)
    
复合条件:
    condition1;condition2       - AND关系
    condition1|condition2       - OR关系

示例:
    "has_item:golden_key:1"                    - 需要1把金钥匙
    "attr:strength:>=:50"                      - 臂力>=50
    "has_item:pass:1;attr:level:>=:10"         - 需要通行证且等级>=10
    "has_skill:qinggong:5|has_item:rope:1"     - 轻功>=5 或 有绳子
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class LockError(Exception):
    """锁解析错误."""
    pass


class LockCondition(ABC):
    """锁条件基类."""
    
    @abstractmethod
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查条件.
        
        Args:
            character: 要检查的角色
            
        Returns:
            (是否通过, 失败原因)
        """
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        """返回字符串表示."""
        pass


@dataclass
class HasItemCondition(LockCondition):
    """拥有物品条件."""
    item_key: str
    quantity: int = 1
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查是否拥有足够物品."""
        # TODO: 实现背包查找逻辑
        # 暂时返回True，等背包系统完成后实现
        return True, ""
    
    def __str__(self) -> str:
        return f"拥有物品 {self.item_key} x{self.quantity}"


@dataclass
class HasSkillCondition(LockCondition):
    """拥有技能条件."""
    skill_key: str
    level: int = 1
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查是否拥有足够等级技能."""
        # TODO: 实现武学系统检查
        return True, ""
    
    def __str__(self) -> str:
        return f"武学 {self.skill_key} 等级>={self.level}"


@dataclass
class AttrCondition(LockCondition):
    """属性比较条件."""
    attr_name: str
    operator: str  # ==, !=, <, <=, >, >=
    value: int | float | str
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查属性是否满足条件."""
        # 获取属性值
        char_value = getattr(character, self.attr_name, None)
        if char_value is None:
            char_value = character.attributes.get(self.attr_name, 0)
        
        # 类型转换
        try:
            if isinstance(self.value, (int, float)):
                char_value = float(char_value) if char_value is not None else 0
                compare_value = float(self.value)
            else:
                char_value = str(char_value) if char_value is not None else ""
                compare_value = str(self.value)
        except (ValueError, TypeError):
            return False, f"属性 {self.attr_name} 类型不匹配"
        
        # 比较操作
        ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
        }
        
        op_func = ops.get(self.operator)
        if not op_func:
            return False, f"未知操作符 {self.operator}"
        
        if op_func(char_value, compare_value):
            return True, ""
        else:
            return False, f"需要 {self.attr_name} {self.operator} {self.value}"
    
    def __str__(self) -> str:
        return f"属性 {self.attr_name} {self.operator} {self.value}"


@dataclass
class TimeCondition(LockCondition):
    """时间条件."""
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查当前时间是否在范围内."""
        # TODO: 实现游戏时间系统
        # 暂时返回True
        return True, ""
    
    def __str__(self) -> str:
        return f"时间 {self.start_time} - {self.end_time}"


@dataclass
class QuestCondition(LockCondition):
    """任务条件."""
    quest_key: str
    status: str  # active, completed, failed
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """检查任务状态."""
        # TODO: 实现任务系统检查
        return True, ""
    
    def __str__(self) -> str:
        status_map = {
            "active": "进行中",
            "completed": "已完成",
            "failed": "已失败"
        }
        return f"任务 {self.quest_key} {status_map.get(self.status, self.status)}"


class AndCondition(LockCondition):
    """AND组合条件."""
    
    def __init__(self, conditions: list[LockCondition]):
        self.conditions = conditions
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """所有条件都必须满足."""
        for condition in self.conditions:
            passed, reason = condition.check(character)
            if not passed:
                return False, reason
        return True, ""
    
    def __str__(self) -> str:
        return " 且 ".join(str(c) for c in self.conditions)


class OrCondition(LockCondition):
    """OR组合条件."""
    
    def __init__(self, conditions: list[LockCondition]):
        self.conditions = conditions
    
    def check(self, character: "Character") -> tuple[bool, str]:
        """任一条件满足即可."""
        all_reasons = []
        for condition in self.conditions:
            passed, reason = condition.check(character)
            if passed:
                return True, ""
            all_reasons.append(reason)
        return False, " 或 ".join(all_reasons)
    
    def __str__(self) -> str:
        return " 或 ".join(str(c) for c in self.conditions)


class ExitLockParser:
    """出口锁解析器."""
    
    # 锁字符串语法正则
    # attr:name:op:value - op可以是==, !=, <=, >=, <, > (按长度降序匹配)
    PATTERN_HAS_ITEM = re.compile(r'^has_item:([^:]+):(\d+)$')
    PATTERN_HAS_SKILL = re.compile(r'^has_skill:([^:]+):(\d+)$')
    # attr:name:op:value - 使用非捕获组 (?:) 来避免额外的组
    PATTERN_ATTR = re.compile(r'^attr:([^:]+):(==|!=|<=|>=|<|>):(.+)$')
    PATTERN_TIME = re.compile(r'^time:(\d{2}:\d{2}):(\d{2}:\d{2})$')
    PATTERN_QUEST = re.compile(r'^quest:([^:]+):(active|completed|failed)$')
    
    @classmethod
    def parse(cls, lock_str: str | None) -> LockCondition | None:
        """解析锁字符串.
        
        Args:
            lock_str: 锁字符串，如 "has_item:key:1;attr:level:>=:10"
            
        Returns:
            LockCondition对象或None
            
        Raises:
            LockError: 解析失败
        """
        if not lock_str or not lock_str.strip():
            return None
        
        lock_str = lock_str.strip()
        
        # 处理OR条件 (优先级低，先分割OR)
        if '|' in lock_str:
            or_parts = lock_str.split('|')
            # 每个OR部分可能包含AND条件
            conditions = [cls._parse_condition_part(part.strip()) for part in or_parts]
            return OrCondition(conditions)
        
        # 没有OR，直接解析
        return cls._parse_condition_part(lock_str)
    
    @classmethod
    def _parse_condition_part(cls, lock_str: str) -> LockCondition:
        """解析条件部分（可能是AND组合或单个条件）."""
        # 处理AND条件
        if ';' in lock_str:
            and_parts = lock_str.split(';')
            conditions = [cls._parse_single(part.strip()) for part in and_parts]
            return AndCondition(conditions)
        
        # 单个条件
        return cls._parse_single(lock_str)
    
    @classmethod
    def _parse_single(cls, lock_str: str) -> LockCondition:
        """解析单个条件."""
        lock_str = lock_str.strip()
        
        # has_item:key:quantity
        match = cls.PATTERN_HAS_ITEM.match(lock_str)
        if match:
            return HasItemCondition(
                item_key=match.group(1),
                quantity=int(match.group(2))
            )
        
        # has_skill:key:level
        match = cls.PATTERN_HAS_SKILL.match(lock_str)
        if match:
            return HasSkillCondition(
                skill_key=match.group(1),
                level=int(match.group(2))
            )
        
        # attr:name:op:value
        match = cls.PATTERN_ATTR.match(lock_str)
        if match:
            value = match.group(3)
            # 尝试转换为数字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # 保持字符串
            
            return AttrCondition(
                attr_name=match.group(1),
                operator=match.group(2),
                value=value
            )
        
        # time:start:end
        match = cls.PATTERN_TIME.match(lock_str)
        if match:
            return TimeCondition(
                start_time=match.group(1),
                end_time=match.group(2)
            )
        
        # quest:key:status
        match = cls.PATTERN_QUEST.match(lock_str)
        if match:
            return QuestCondition(
                quest_key=match.group(1),
                status=match.group(2)
            )
        
        raise LockError(f"无法解析锁字符串: {lock_str}")

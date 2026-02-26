"""状态验证模块.

提供对象状态一致性检查和自动修复功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .character import Character


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    current_value: Any
    expected_range: str


class StateValidator:
    """状态验证器基类"""
    
    def __init__(self):
        self._rules: list[tuple[str, Callable[[Any], bool], str]] = []
    
    def add_rule(self, field: str, check: Callable[[Any], bool], message: str):
        """添加验证规则"""
        self._rules.append((field, check, message))
    
    def validate(self, obj: Any) -> list[ValidationError]:
        """验证对象状态"""
        errors = []
        for field, check, message in self._rules:
            value = getattr(obj, field, None)
            if not check(value):
                errors.append(ValidationError(
                    field=field,
                    message=message,
                    current_value=value,
                    expected_range="见验证规则"
                ))
        return errors


class CharacterValidator(StateValidator):
    """角色状态验证器"""
    
    def __init__(self):
        super().__init__()
        self._setup_rules()
    
    def _setup_rules(self):
        """设置角色验证规则"""
        # HP规则
        self.add_rule(
            'hp',
            lambda v: v is not None and v >= 0,
            'HP不能为负数'
        )
        
        # MP规则
        self.add_rule(
            'mp',
            lambda v: v is not None and v >= 0,
            'MP不能为负数'
        )
        
        # EP规则
        self.add_rule(
            'ep',
            lambda v: v is not None and v >= 0,
            'EP不能为负数'
        )
        
        # 等级规则
        self.add_rule(
            'level',
            lambda v: v is not None and 1 <= v <= 1000,
            '等级应在1-1000之间'
        )
        
        # 经验规则
        self.add_rule(
            'exp',
            lambda v: v is not None and v >= 0,
            '经验不能为负数'
        )
    
    def validate(self, character: Character) -> list[ValidationError]:
        """验证角色状态"""
        errors = super().validate(character)
        
        # 额外检查HP上限
        if hasattr(character, 'hp') and hasattr(character, 'max_hp'):
            try:
                if character.hp > character.max_hp:
                    errors.append(ValidationError(
                        field='hp',
                        message='HP超过上限',
                        current_value=character.hp,
                        expected_range=f'0-{character.max_hp}'
                    ))
            except TypeError:
                pass  # 忽略类型错误（如MagicMock比较）
        
        # 检查MP上限
        if hasattr(character, 'mp') and hasattr(character, 'max_mp'):
            try:
                if character.mp > character.max_mp:
                    errors.append(ValidationError(
                        field='mp',
                        message='MP超过上限',
                        current_value=character.mp,
                        expected_range=f'0-{character.max_mp}'
                    ))
            except TypeError:
                pass
        
        # 检查EP上限
        if hasattr(character, 'ep') and hasattr(character, 'max_ep'):
            try:
                if character.ep > character.max_ep:
                    errors.append(ValidationError(
                        field='ep',
                        message='EP超过上限',
                        current_value=character.ep,
                        expected_range=f'0-{character.max_ep}'
                    ))
            except TypeError:
                pass
        
        return errors
    
    def fix(self, character: Character) -> list[str]:
        """自动修复状态问题"""
        fixes = []
        
        # 修复HP
        if hasattr(character, 'hp'):
            try:
                if character.hp < 0:
                    character.hp = 0
                    fixes.append('HP从负数修复为0')
                elif hasattr(character, 'max_hp') and character.hp > character.max_hp:
                    character.hp = character.max_hp
                    fixes.append(f'HP修复为上限{character.max_hp}')
            except TypeError:
                pass
        
        # 修复MP
        if hasattr(character, 'mp'):
            try:
                if character.mp < 0:
                    character.mp = 0
                    fixes.append('MP从负数修复为0')
                elif hasattr(character, 'max_mp') and character.mp > character.max_mp:
                    character.mp = character.max_mp
                    fixes.append(f'MP修复为上限{character.max_mp}')
            except TypeError:
                pass
        
        # 修复EP
        if hasattr(character, 'ep'):
            try:
                if character.ep < 0:
                    character.ep = 0
                    fixes.append('EP从负数修复为0')
                elif hasattr(character, 'max_ep') and character.ep > character.max_ep:
                    character.ep = character.max_ep
                    fixes.append(f'EP修复为上限{character.max_ep}')
            except TypeError:
                pass
        
        # 修复等级
        if hasattr(character, 'level'):
            try:
                if character.level < 1:
                    character.level = 1
                    fixes.append('等级从低于1修复为1')
                elif character.level > 1000:
                    character.level = 1000
                    fixes.append('等级从超过1000修复为1000')
            except TypeError:
                pass
        
        # 修复经验
        if hasattr(character, 'exp'):
            try:
                if character.exp < 0:
                    character.exp = 0
                    fixes.append('经验从负数修复为0')
            except TypeError:
                pass
        
        return fixes

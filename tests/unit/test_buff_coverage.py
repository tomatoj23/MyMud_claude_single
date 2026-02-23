"""Buff 模块覆盖率补充测试."""
import pytest
from unittest.mock import Mock

from src.game.combat.buff import (
    create_poison_buff,
    create_regen_buff,
    BuffManager,
)


class TestBuffFactories:
    """测试 BUFF 工厂函数的内部回调."""

    @pytest.mark.asyncio
    async def test_poison_buff_on_tick(self):
        """测试中毒BUFF的on_tick回调被执行."""
        character = Mock()
        character.hp = 100
        
        # 创建中毒buff
        buff = create_poison_buff(damage_per_tick=10)
        
        # 应用buff
        manager = BuffManager(character)
        await manager.add(buff)
        
        # 执行tick，应该触发on_tick
        await manager.tick()
        
        # 验证扣血被调用
        character.modify_hp.assert_called_with(-10)

    @pytest.mark.asyncio
    async def test_regen_buff_on_tick(self):
        """测试恢复BUFF的on_tick回调被执行."""
        character = Mock()
        
        # 创建恢复buff
        buff = create_regen_buff(heal_per_tick=15)
        
        # 应用buff
        manager = BuffManager(character)
        await manager.add(buff)
        
        # 执行tick，应该触发on_tick
        await manager.tick()
        
        # 验证回血被调用
        character.modify_hp.assert_called_with(15)

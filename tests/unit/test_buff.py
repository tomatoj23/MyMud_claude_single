"""BUFF/DEBUFF系统单元测试.

测试Buff和BuffManager类.
"""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from src.game.combat.buff import Buff, BuffManager, BuffType


class TestBuffType:
    """BuffType枚举测试."""

    def test_buff_type_values(self):
        """测试BUFF类型值."""
        assert BuffType.BUFF.value == "buff"
        assert BuffType.DEBUFF.value == "debuff"
        assert BuffType.NEUTRAL.value == "neutral"


class TestBuff:
    """Buff类测试."""

    @pytest.fixture
    def basic_buff(self):
        """创建基础BUFF."""
        return Buff(
            key="test_buff",
            name="测试BUFF",
            duration=5.0,
            buff_type=BuffType.BUFF,
            stats_mod={"strength": 10}
        )

    def test_buff_init(self, basic_buff):
        """测试Buff初始化."""
        assert basic_buff.key == "test_buff"
        assert basic_buff.name == "测试BUFF"
        assert basic_buff.duration == 5.0
        assert basic_buff.buff_type == BuffType.BUFF
        assert basic_buff.stats_mod == {"strength": 10}
        assert basic_buff.stack_limit == 1  # 默认
        assert basic_buff.stacks == 1  # 默认

    def test_buff_init_defaults(self):
        """测试Buff默认参数."""
        buff = Buff(key="simple", name="简单BUFF", duration=1.0)
        
        assert buff.buff_type == BuffType.NEUTRAL
        assert buff.stats_mod == {}
        assert buff.stack_limit == 1

    def test_buff_is_expired_false(self, basic_buff):
        """测试未过期BUFF."""
        assert basic_buff.is_expired() is False

    def test_buff_is_expired_true(self, basic_buff):
        """测试过期BUFF."""
        # 创建一个已过期的时间
        basic_buff.expires_at = time.time() - 1.0
        assert basic_buff.is_expired() is True

    def test_buff_is_expired_with_time(self, basic_buff):
        """测试指定时间检查过期."""
        now = time.time()
        
        # 未来时间不过期
        assert basic_buff.is_expired(now) is False
        
        # 过去时间过期
        assert basic_buff.is_expired(now + 10.0) is True

    def test_buff_get_remaining_time(self, basic_buff):
        """测试获取剩余时间."""
        remaining = basic_buff.get_remaining_time()
        
        assert remaining > 4.0  # 接近5秒
        assert remaining <= 5.0

    def test_buff_get_remaining_time_expired(self, basic_buff):
        """测试过期BUFF剩余时间为0."""
        basic_buff.expires_at = time.time() - 1.0
        
        assert basic_buff.get_remaining_time() == 0.0

    @pytest.mark.asyncio
    async def test_buff_apply(self):
        """测试BUFF应用回调."""
        callback_called = False
        
        def on_apply(char):
            nonlocal callback_called
            callback_called = True
        
        buff = Buff(
            key="test",
            name="测试",
            duration=1.0,
            on_apply=on_apply
        )
        
        char = Mock()
        await buff.apply(char)
        
        assert callback_called is True

    @pytest.mark.asyncio
    async def test_buff_tick(self):
        """测试BUFF tick回调."""
        tick_count = 0
        
        def on_tick(char):
            nonlocal tick_count
            tick_count += 1
        
        buff = Buff(
            key="test",
            name="测试",
            duration=1.0,
            on_tick=on_tick
        )
        
        char = Mock()
        await buff.tick(char)
        
        assert tick_count == 1

    @pytest.mark.asyncio
    async def test_buff_remove(self):
        """测试BUFF移除回调."""
        callback_called = False
        
        def on_remove(char):
            nonlocal callback_called
            callback_called = True
        
        buff = Buff(
            key="test",
            name="测试",
            duration=1.0,
            on_remove=on_remove
        )
        
        char = Mock()
        await buff.remove(char)
        
        assert callback_called is True


class TestBuffManager:
    """BuffManager类测试."""

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        return Mock()

    @pytest.fixture
    def manager(self, character):
        """创建BuffManager实例."""
        return BuffManager(character)

    @pytest.fixture
    def test_buff(self):
        """创建测试BUFF."""
        return Buff(
            key="test_buff",
            name="测试BUFF",
            duration=5.0,
            stats_mod={"strength": 10}
        )

    def test_manager_init(self, character):
        """测试BuffManager初始化."""
        manager = BuffManager(character)
        
        assert manager.character == character
        assert manager._buffs == {}

    @pytest.mark.asyncio
    async def test_add_new_buff(self, manager, test_buff):
        """测试添加新BUFF."""
        result = await manager.add(test_buff)
        
        assert result is True
        assert "test_buff" in manager._buffs
        assert manager._buffs["test_buff"] == test_buff

    @pytest.mark.asyncio
    async def test_add_stack_buff(self, manager, test_buff):
        """测试BUFF叠加."""
        test_buff.stack_limit = 3
        
        # 第一次添加
        await manager.add(test_buff)
        
        # 第二次添加相同BUFF，应该叠加
        buff2 = Buff(
            key="test_buff",
            name="测试BUFF",
            duration=5.0,
            stats_mod={"strength": 10},
            stack_limit=3
        )
        result = await manager.add(buff2)
        
        assert result is True
        assert manager._buffs["test_buff"].stacks == 2

    @pytest.mark.asyncio
    async def test_add_stack_limit(self, manager, test_buff):
        """测试BUFF叠加上限."""
        test_buff.stack_limit = 2
        
        # 添加3次，但上限是2
        for _ in range(3):
            buff = Buff(
                key="test_buff",
                name="测试BUFF",
                duration=5.0,
                stack_limit=2
            )
            await manager.add(buff)
        
        assert manager._buffs["test_buff"].stacks == 2  # 不超过上限

    @pytest.mark.asyncio
    async def test_add_refresh_duration(self, manager, test_buff):
        """测试叠加时刷新持续时间."""
        test_buff.stack_limit = 2
        
        # 第一个BUFF设置为即将过期
        test_buff.expires_at = time.time() + 1.0
        await manager.add(test_buff)
        
        # 添加第二个刷新持续时间
        buff2 = Buff(
            key="test_buff",
            name="测试BUFF",
            duration=10.0,  # 更长的持续时间
            stack_limit=2
        )
        await manager.add(buff2)
        
        # 持续时间应该被刷新
        assert manager._buffs["test_buff"].get_remaining_time() > 5.0

    @pytest.mark.asyncio
    async def test_remove_existing_buff(self, manager, test_buff):
        """测试移除存在的BUFF."""
        await manager.add(test_buff)
        
        result = await manager.remove("test_buff")
        
        assert result is True
        assert "test_buff" not in manager._buffs

    @pytest.mark.asyncio
    async def test_remove_nonexistent_buff(self, manager):
        """测试移除不存在的BUFF."""
        result = await manager.remove("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_tick_no_buffs(self, manager):
        """测试空BUFF列表tick."""
        messages = await manager.tick()
        
        assert messages == []

    @pytest.mark.asyncio
    async def test_tick_with_buffs(self, manager, test_buff):
        """测试有BUFF时的tick."""
        await manager.add(test_buff)
        
        messages = await manager.tick()
        
        # 未过期，应该没有移除消息
        assert "测试BUFF效果消失了" not in messages

    @pytest.mark.asyncio
    async def test_tick_remove_expired(self, manager):
        """测试tick移除过期BUFF."""
        # 创建一个已过期或即将过期的BUFF
        buff = Buff(
            key="expired",
            name="过期BUFF",
            duration=0.001  # 极短的持续时间
        )
        await manager.add(buff)
        
        # 等待过期
        time.sleep(0.002)
        
        messages = await manager.tick()
        
        assert "过期BUFF效果消失了。" in messages
        assert "expired" not in manager._buffs

    @pytest.mark.asyncio
    async def test_tick_execute_on_tick(self, manager):
        """测试tick执行BUFF的on_tick回调."""
        tick_called = False
        
        def on_tick(char):
            nonlocal tick_called
            tick_called = True
        
        buff = Buff(
            key="tick_test",
            name="Tick测试",
            duration=5.0,
            on_tick=on_tick
        )
        await manager.add(buff)
        
        await manager.tick()
        
        assert tick_called is True

    def test_get_stats_modifier_empty(self, manager):
        """测试无BUFF时的属性修正."""
        mods = manager.get_stats_modifier()
        
        assert mods == {}

    def test_get_stats_modifier_single(self, manager, test_buff):
        """测试单个BUFF的属性修正."""
        import asyncio
        asyncio.run(manager.add(test_buff))
        
        mods = manager.get_stats_modifier()
        
        assert mods == {"strength": 10}

    def test_get_stats_modifier_stacked(self, manager):
        """测试叠加BUFF的属性修正."""
        import asyncio
        
        buff = Buff(
            key="stacked",
            name="叠加BUFF",
            duration=5.0,
            stats_mod={"strength": 5},
            stack_limit=3
        )
        
        # 添加3层
        for _ in range(3):
            b = Buff(
                key="stacked",
                name="叠加BUFF",
                duration=5.0,
                stats_mod={"strength": 5},
                stack_limit=3
            )
            asyncio.run(manager.add(b))
        
        mods = manager.get_stats_modifier()
        
        # 3层，每层+5力量
        assert mods["strength"] == 15

    def test_get_stats_modifier_multiple_buffs(self, manager):
        """测试多个不同BUFF的属性修正."""
        import asyncio
        
        buff1 = Buff(key="buff1", name="力量BUFF", duration=5.0, stats_mod={"strength": 10})
        buff2 = Buff(key="buff2", name="敏捷BUFF", duration=5.0, stats_mod={"agility": 5})
        
        asyncio.run(manager.add(buff1))
        asyncio.run(manager.add(buff2))
        
        mods = manager.get_stats_modifier()
        
        assert mods["strength"] == 10
        assert mods["agility"] == 5

    def test_has_buff_true(self, manager, test_buff):
        """测试检查存在BUFF."""
        import asyncio
        asyncio.run(manager.add(test_buff))
        
        assert manager.has_buff("test_buff") is True

    def test_has_buff_false(self, manager):
        """测试检查不存在BUFF."""
        assert manager.has_buff("nonexistent") is False

    def test_has_buff_expired(self, manager):
        """测试检查过期BUFF返回False."""
        import asyncio
        
        buff = Buff(
            key="expired",
            name="过期",
            duration=0.001
        )
        asyncio.run(manager.add(buff))
        time.sleep(0.002)
        
        assert manager.has_buff("expired") is False

    def test_get_buffs_all(self, manager, test_buff):
        """测试获取所有BUFF."""
        import asyncio
        asyncio.run(manager.add(test_buff))
        
        buffs = manager.get_buffs()
        
        assert len(buffs) == 1
        assert buffs[0].key == "test_buff"

    def test_get_buffs_by_type(self, manager):
        """测试按类型获取BUFF."""
        import asyncio
        
        buff1 = Buff(key="b1", name="增益", duration=5.0, buff_type=BuffType.BUFF)
        buff2 = Buff(key="b2", name="减益", duration=5.0, buff_type=BuffType.DEBUFF)
        
        asyncio.run(manager.add(buff1))
        asyncio.run(manager.add(buff2))
        
        buffs = manager.get_buffs(BuffType.BUFF)
        
        assert len(buffs) == 1
        assert buffs[0].key == "b1"

    def test_get_buffs_excludes_expired(self, manager):
        """测试获取BUFF时排除过期."""
        import asyncio
        
        buff1 = Buff(key="active", name="活跃", duration=10.0)
        buff2 = Buff(key="expired", name="过期", duration=0.001)
        
        asyncio.run(manager.add(buff1))
        asyncio.run(manager.add(buff2))
        
        time.sleep(0.002)
        
        buffs = manager.get_buffs()
        
        assert len(buffs) == 1
        assert buffs[0].key == "active"

    def test_clear(self, manager, test_buff):
        """测试清空所有BUFF."""
        import asyncio
        asyncio.run(manager.add(test_buff))
        
        manager.clear()
        
        assert manager._buffs == {}

    def test_get_summary_empty(self, manager):
        """测试空BUFF列表摘要."""
        summary = manager.get_summary()
        
        assert summary == []

    def test_get_summary(self, manager, test_buff):
        """测试BUFF摘要."""
        import asyncio
        asyncio.run(manager.add(test_buff))
        
        summary = manager.get_summary()
        
        assert len(summary) == 1
        assert summary[0]["key"] == "test_buff"
        assert summary[0]["name"] == "测试BUFF"
        assert summary[0]["type"] == "neutral"
        assert summary[0]["stacks"] == 1
        assert "remaining" in summary[0]

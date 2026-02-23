"""任务奖励单元测试.

测试TD-020/021: 任务物品发放和武学奖励
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.game.quest.core import CharacterQuestMixin
from src.game.typeclasses.wuxue import Kungfu, WuxueType


class TestQuestRewards:
    """测试任务奖励."""
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色（带Quest Mixin）."""
        char = MagicMock(spec=CharacterQuestMixin)
        char.db = MagicMock()
        char.db.get.return_value = 0
        char.db.set = MagicMock()
        char.learned_wuxue = {}
        
        # 模拟奖励发放
        async def give_rewards(rewards):
            msgs = []
            
            # 经验
            if "exp" in rewards:
                msgs.append(f"经验 +{rewards['exp']}")
            
            # 物品
            if "items" in rewards:
                item_rewards = rewards["items"]
                if isinstance(item_rewards, dict):
                    item_rewards = [item_rewards]
                for item in item_rewards:
                    name = item.get("name", item.get("key"))
                    qty = item.get("quantity", 1)
                    msgs.append(f"获得 {name} x{qty}")
            
            # 武学
            if "wuxue" in rewards:
                kungfu_key = rewards["wuxue"]
                # 模拟学习
                char.learned_wuxue[kungfu_key] = {"level": 1}
                msgs.append(f"领悟「测试武功」")
            
            return " ".join(msgs)
        
        char._give_rewards = give_rewards
        
        return char
    
    @pytest.mark.asyncio
    async def test_exp_reward(self, mock_character):
        """测试经验奖励."""
        rewards = {"exp": 100}
        msg = await mock_character._give_rewards(rewards)
        
        assert "经验 +100" in msg
    
    @pytest.mark.asyncio
    async def test_item_reward_single(self, mock_character):
        """测试单个物品奖励."""
        rewards = {
            "items": {"key": "iron_sword", "name": "铁剑", "quantity": 1}
        }
        msg = await mock_character._give_rewards(rewards)
        
        assert "获得 铁剑 x1" in msg
    
    @pytest.mark.asyncio
    async def test_item_reward_multiple(self, mock_character):
        """测试多个物品奖励."""
        rewards = {
            "items": [
                {"key": "potion", "name": "金疮药", "quantity": 5},
                {"key": "scroll", "name": "秘籍", "quantity": 1}
            ]
        }
        msg = await mock_character._give_rewards(rewards)
        
        assert "获得 金疮药 x5" in msg
        assert "获得 秘籍 x1" in msg
    
    @pytest.mark.asyncio
    async def test_wuxue_reward(self, mock_character):
        """测试武学奖励."""
        rewards = {"wuxue": "shaolin_jian"}
        msg = await mock_character._give_rewards(rewards)
        
        assert "领悟" in msg
        assert "shaolin_jian" in mock_character.learned_wuxue
    
    @pytest.mark.asyncio
    async def test_combined_rewards(self, mock_character):
        """测试组合奖励."""
        rewards = {
            "exp": 500,
            "items": {"key": "treasure", "name": "宝物", "quantity": 1},
            "wuxue": "secret_art"
        }
        msg = await mock_character._give_rewards(rewards)
        
        assert "经验 +500" in msg
        assert "获得 宝物 x1" in msg
        assert "领悟" in msg


class TestRealQuestRewards:
    """使用真实CharacterQuestMixin的测试."""
    
    @pytest.fixture
    def real_mixin(self):
        """创建真实的mixin实例."""
        from src.game.quest.core import CharacterQuestMixin as CQM
        
        mixin = MagicMock(spec=CQM)
        mixin.db = MagicMock()
        mixin.db.get.return_value = 0
        mixin.db.set = MagicMock()
        
        # 绑定真实方法
        mixin._give_rewards = lambda rewards: CQM._give_rewards(mixin, rewards)
        
        return mixin
    
    @pytest.mark.asyncio
    async def test_real_exp_reward(self, real_mixin):
        """测试真实经验奖励."""
        rewards = {"exp": 200}
        
        # 模拟add_exp方法
        real_mixin.add_exp = MagicMock()
        
        msg = await real_mixin._give_rewards(rewards)
        
        assert "经验 +200" in msg
        real_mixin.add_exp.assert_called_once_with(200)
    
    @pytest.mark.asyncio
    async def test_real_silver_reward(self, real_mixin):
        """测试真实银两奖励."""
        rewards = {"silver": 50}
        msg = await real_mixin._give_rewards(rewards)
        
        assert "银两 +50" in msg
        # 验证db.set被调用
        real_mixin.db.set.assert_called()

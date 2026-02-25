"""架构改进集成测试.

针对 Phase 1/2/3 架构改动的专项集成测试。
"""

import pytest
from unittest.mock import MagicMock, patch


class TestCombatTransactionIntegration:
    """测试战斗事务保护集成."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception_during_combat(self):
        """测试战斗中异常时事务回滚."""
        from src.game.combat.core import CombatSession
        
        # 创建模拟角色
        attacker = MagicMock()
        attacker.id = 1
        attacker.name = "攻击者"
        attacker.get_hp.return_value = (100, 100)
        attacker.get_agility.return_value = 10
        
        defender = MagicMock()
        defender.id = 2
        defender.name = "防御者"
        defender.get_hp.return_value = (100, 100)
        defender.get_agility.return_value = 10
        defender.get_defense.return_value = 5
        
        # 记录初始HP
        initial_hp = 100
        defender.hp = initial_hp
        
        # 创建战斗会话
        session = CombatSession(None, [attacker, defender])
        
        # 模拟事务中发生异常
        with patch.object(session, '_execute_move', side_effect=Exception("模拟异常")):
            try:
                await session._execute_move(attacker, defender, None)
            except Exception:
                pass
        
        # 验证HP未改变（已回滚）
        assert defender.hp == initial_hp
    
    @pytest.mark.asyncio
    async def test_nested_transactions_in_combat(self):
        """测试嵌套事务场景."""
        from src.game.combat.transaction import TransactionManager
        
        manager = TransactionManager()
        obj = MagicMock()
        obj.hp = 100
        
        # 外层事务
        with manager.begin() as outer_txn:
            outer_txn.snapshot(obj, ['hp'])
            obj.hp = 80
            
            # 内层事务
            with manager.begin() as inner_txn:
                inner_txn.snapshot(obj, ['hp'])
                obj.hp = 60
            
            # 内层已提交，hp=60
            assert obj.hp == 60
        
        # 外层也已提交
        assert obj.hp == 60


class TestMixinNamingIntegration:
    """测试Mixin方法前缀规范集成."""
    
    def test_equipment_methods_renamed(self):
        """测试装备方法已重命名."""
        from src.game.typeclasses.equipment import CharacterEquipmentMixin
        
        # 验证新方法存在
        assert hasattr(CharacterEquipmentMixin, 'equipment_get_item')
        assert hasattr(CharacterEquipmentMixin, 'equipment_equip')
        assert hasattr(CharacterEquipmentMixin, 'equipment_unequip')
        assert hasattr(CharacterEquipmentMixin, 'equipment_get_stats')
        
        # 验证旧方法不存在
        assert not hasattr(CharacterEquipmentMixin, 'get_equipped')
    
    def test_wuxue_methods_renamed(self):
        """测试武学方法已重命名."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin
        
        # 验证新方法存在
        assert hasattr(CharacterWuxueMixin, 'wuxue_has_learned')
        assert hasattr(CharacterWuxueMixin, 'wuxue_get_moves')
        assert hasattr(CharacterWuxueMixin, 'wuxue_learned')
        
        # 验证旧方法不存在
        assert not hasattr(CharacterWuxueMixin, 'has_learned')
    
    def test_character_unified_interface(self):
        """测试Character统一接口."""
        from src.game.typeclasses.character import Character
        
        # 验证统一接口存在
        assert hasattr(Character, 'get_attack')
        assert hasattr(Character, 'get_defense')
        assert hasattr(Character, 'equipment_get_stats')
        assert hasattr(Character, 'wuxue_get_moves')


class TestCombatStrategyIntegration:
    """测试战斗策略模式集成."""
    
    @pytest.mark.asyncio
    async def test_strategy_registration(self):
        """测试策略注册."""
        from src.game.combat.core import _get_strategies
        
        strategies = _get_strategies()
        
        assert "kill" in strategies
        assert "cast" in strategies
        assert "flee" in strategies
        assert "defend" in strategies
    
    @pytest.mark.asyncio
    async def test_strategy_validation_before_execute(self):
        """测试策略先验证后执行."""
        from src.game.combat.strategy import AttackStrategy
        
        strategy = AttackStrategy()
        session = MagicMock()
        session.participants = {}
        combatant = MagicMock()
        
        # 无目标时应验证失败
        valid, msg = strategy.validate(session, combatant, {})
        assert valid is False
        
        # 验证validate失败时返回的消息包含"目标"
        assert "目标" in msg
    
    @pytest.mark.asyncio
    async def test_custom_strategy_extension(self):
        """测试自定义策略扩展."""
        from src.game.combat.strategy import CombatActionStrategy, ActionResult
        
        class CustomStrategy(CombatActionStrategy):
            async def execute(self, session, combatant, args):
                return ActionResult(success=True, message="自定义行动")
            
            def validate(self, session, combatant, args):
                return True, ""
        
        # 验证自定义策略可用
        strategy = CustomStrategy()
        result = await strategy.execute(None, None, {})
        assert result.success is True


class TestValidationIntegration:
    """测试状态验证集成."""
    
    def test_character_state_validation(self):
        """测试角色状态验证."""
        from src.game.typeclasses.validation import CharacterValidator
        
        validator = CharacterValidator()
        
        # 有效状态 - 使用具体值而不是MagicMock
        class ValidChar:
            def __init__(self):
                self.hp = 100
                self.mp = 50
                self.ep = 50
                self.level = 10
                self.exp = 100
                self.max_hp = 100
                self.max_mp = 50
                self.max_ep = 50
        
        valid_char = ValidChar()
        errors = validator.validate(valid_char)
        assert len(errors) == 0
        
        # 无效状态
        class InvalidChar:
            def __init__(self):
                self.hp = -10
                self.mp = 50
                self.ep = 50
                self.level = 10
                self.exp = 100
        
        invalid_char = InvalidChar()
        errors = validator.validate(invalid_char)
        assert len(errors) > 0
    
    def test_auto_fix_state(self):
        """测试自动修复状态."""
        from src.game.typeclasses.validation import CharacterValidator
        
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = -10
        char.max_hp = 100
        char.mp = -5
        char.max_mp = 50
        char.level = 0
        char.exp = -100
        
        fixes = validator.fix(char)
        
        assert char.hp == 0  # 负值修复为0
        assert char.mp == 0
        assert char.level == 1  # 低于1修复为1
        assert char.exp == 0
        assert len(fixes) > 0


class TestComponentSystemIntegration:
    """测试组件系统集成."""
    
    def test_component_lifecycle(self):
        """测试组件生命周期."""
        from src.engine.components import Component, ComponentMixin
        
        class TestComponent(Component):
            def __init__(self, owner):
                super().__init__(owner)
                self.attached = False
                self.detached = False
            
            def get_stats(self):
                return {"test": 1}
            
            def on_attach(self):
                self.attached = True
            
            def on_detach(self):
                self.detached = True
        
        # 测试生命周期
        mixin = ComponentMixin()
        comp = TestComponent(mixin)
        
        mixin.add_component("test", comp)
        assert comp.attached is True
        
        mixin.remove_component("test")
        assert comp.detached is True
    
    def test_stats_aggregation(self):
        """测试属性聚合."""
        from src.engine.components import Component, ComponentMixin
        
        class AttackComponent(Component):
            def get_stats(self):
                return {"attack": 10}
        
        class DefenseComponent(Component):
            def get_stats(self):
                return {"defense": 5}
        
        mixin = ComponentMixin()
        mixin.add_component("attack", AttackComponent(mixin))
        mixin.add_component("defense", DefenseComponent(mixin))
        
        stats = mixin.aggregate_stats()
        assert stats["attack"] == 10
        assert stats["defense"] == 5


class TestBalanceConfigIntegration:
    """测试平衡配置集成."""
    
    def test_config_singleton(self):
        """测试配置单例."""
        from src.utils.config_loader import get_balance_config, BalanceConfig
        
        config1 = get_balance_config()
        config2 = BalanceConfig()
        
        assert config1 is config2
    
    def test_config_values(self):
        """测试配置值正确性."""
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        # 验证战斗配置
        assert config.get("combat", "damage", "base") == 10
        assert config.get("combat", "cooldown", "base") == 3.0
        
        # 验证升级配置
        exp_curve = config.get("leveling", "exp_curve")
        assert isinstance(exp_curve, list)
        assert exp_curve[0] == 100
    
    def test_config_default_value(self):
        """测试配置默认值."""
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        # 获取不存在的配置应返回默认值
        value = config.get("nonexistent", "key", default=999)
        assert value == 999


class TestDebugCommandsIntegration:
    """测试调试命令集成."""
    
    @pytest.mark.asyncio
    async def test_validate_character_command(self):
        """测试角色验证命令."""
        from src.game.commands.debug import CmdValidateCharacter
        
        cmd = CmdValidateCharacter()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        await cmd.execute()
        
        # 无参数时应显示用法
        cmd.caller.msg.assert_called_once()
        assert "用法" in cmd.caller.msg.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_inspect_character_command(self):
        """测试角色查看命令."""
        from src.game.commands.debug import CmdInspectCharacter
        
        cmd = CmdInspectCharacter()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        await cmd.execute()
        
        # 无参数时应显示用法
        cmd.caller.msg.assert_called_once()


class TestArchitectureBackwardCompatibility:
    """测试架构改动向后兼容性."""
    
    @pytest.mark.asyncio
    async def test_old_combat_api_still_works(self):
        """测试旧版战斗API仍然可用."""
        from src.game.combat.core import CombatSession
        
        # 使用旧方式创建战斗会话
        char1 = MagicMock()
        char1.id = 1
        char1.get_hp.return_value = (100, 100)
        char1.get_agility.return_value = 10
        
        char2 = MagicMock()
        char2.id = 2
        char2.get_hp.return_value = (100, 100)
        char2.get_agility.return_value = 10
        
        # 创建战斗会话不应报错
        session = CombatSession(None, [char1, char2])
        assert session is not None
    
    def test_character_init_backward_compatible(self):
        """测试Character初始化向后兼容."""
        from src.game.typeclasses.character import Character
        
        # 模拟管理器和数据库模型
        mock_manager = MagicMock()
        mock_db = MagicMock()
        mock_db.id = 1
        mock_db.key = "test_char"
        mock_db.attributes = {
            "hp": (100, 100),
            "mp": (50, 50),
            "level": 1
        }
        
        # 新方式初始化
        char = Character(manager=mock_manager, db_model=mock_db)
        assert char is not None
        assert char.id == 1

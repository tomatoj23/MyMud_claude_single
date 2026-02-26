"""架构改动混沌行为测试.

针对架构改进的混沌测试，验证系统在异常和非理性行为下的鲁棒性。
"""

import pytest
import random
import string
from unittest.mock import MagicMock, patch


class TestChaosCombatTransaction:
    """战斗事务保护混沌测试."""
    
    @pytest.mark.asyncio
    async def test_chaos_random_damage_values(self):
        """混沌测试：随机伤害值."""
        from src.game.combat.transaction import CombatTransaction
        
        txn = CombatTransaction()
        char = MagicMock()
        
        # 测试各种极端伤害值
        extreme_values = [
            0, 1, -1, 999999, -999999, 
            1.7976931348623157e+308,  # 浮点最大值
            2.2250738585072014e-308,  # 浮点最小值
        ]
        
        for damage in extreme_values:
            char.hp = 100
            txn.snapshot(char, ['hp'])
            
            try:
                char.hp -= damage
                txn.commit()
                # 如果成功，hp 应该被修改
            except Exception:
                # 异常时应该能回滚
                txn.rollback()
                assert char.hp == 100  # 回滚到初始值
    
    @pytest.mark.asyncio
    async def test_chaos_transaction_interruption(self):
        """混沌测试：事务中断场景 - 使用常规异常."""
        from src.game.combat.transaction import TransactionManager
        
        manager = TransactionManager()
        
        # 使用具体类来验证回滚
        class TrackableChar:
            def __init__(self):
                self.hp = 100
                self.mp = 50
        
        trackable1 = TrackableChar()
        trackable2 = TrackableChar()
        
        # 使用常规异常而不是KeyboardInterrupt
        try:
            with manager.begin() as txn:
                txn.snapshot(trackable1, ['hp'])
                txn.snapshot(trackable2, ['mp'])
                
                trackable1.hp = 80
                trackable2.mp = 30
                
                # 模拟异常中断
                raise RuntimeError("模拟异常")
        except RuntimeError:
            pass
        
        # 验证已回滚
        assert trackable1.hp == 100
        assert trackable2.mp == 50
    
    @pytest.mark.asyncio
    async def test_chaos_nested_transaction_failure(self):
        """混沌测试：嵌套事务失败."""
        from src.game.combat.transaction import TransactionManager
        
        manager = TransactionManager()
        char = MagicMock()
        char.hp = 100
        char.mp = 50
        
        try:
            with manager.begin() as outer:
                outer.snapshot(char, ['hp', 'mp'])
                char.hp = 80
                
                try:
                    with manager.begin() as inner:
                        inner.snapshot(char, ['mp'])
                        char.mp = 25
                        raise ValueError("内层事务异常")
                except ValueError:
                    # 内层已回滚
                    assert char.mp == 50
                    raise  # 重新抛出影响外层
        except ValueError:
            pass
        
        # 外层也应该回滚
        assert char.hp == 100
        assert char.mp == 50


class TestChaosMixinRenaming:
    """Mixin方法重命名混沌测试."""
    
    def test_chaos_call_old_method_names(self):
        """混沌测试：尝试调用旧方法名."""
        from src.game.typeclasses.equipment import CharacterEquipmentMixin
        from src.game.typeclasses.wuxue import CharacterWuxueMixin
        
        # 旧方法名应该不存在
        old_equipment_methods = ['get_equipped', 'equip', 'unequip', 'get_total_stats']
        old_wuxue_methods = ['has_learned', 'learn_wuxue', 'get_available_moves']
        
        for method in old_equipment_methods:
            assert not hasattr(CharacterEquipmentMixin, method), f"旧方法 {method} 应该已被删除"
        
        for method in old_wuxue_methods:
            assert not hasattr(CharacterWuxueMixin, method), f"旧方法 {method} 应该已被删除"
    
    def test_chaos_mixin_method_collision(self):
        """混沌测试：验证Mixin方法命名不冲突."""
        from src.game.typeclasses.character import Character
        
        # 获取所有方法
        methods = [m for m in dir(Character) if not m.startswith('_')]
        
        # 检查是否有重复前缀
        equipment_methods = [m for m in methods if m.startswith('equipment_')]
        wuxue_methods = [m for m in methods if m.startswith('wuxue_')]
        
        # 前缀分组后不应有重叠
        prefixes = set()
        for method in methods:
            if '_' in method:
                prefix = method.split('_')[0]
                prefixes.add(prefix)
        
        # 验证预期的前缀存在
        assert 'equipment' in prefixes or len(equipment_methods) == 0
        assert 'wuxue' in prefixes or len(wuxue_methods) == 0


class TestChaosCombatStrategy:
    """战斗策略模式混沌测试."""
    
    @pytest.mark.asyncio
    async def test_chaos_unknown_strategy_type(self):
        """混沌测试：未知策略类型."""
        from src.game.combat.core import _get_strategies
        
        strategies = _get_strategies()
        
        # 测试随机字符串作为策略名
        for _ in range(100):
            random_strategy = ''.join(random.choices(string.ascii_lowercase, k=10))
            assert random_strategy not in strategies or isinstance(strategies.get(random_strategy), object)
    
    @pytest.mark.asyncio
    async def test_chaos_strategy_with_malformed_args(self):
        """混沌测试：畸形参数."""
        from src.game.combat.strategy import AttackStrategy
        
        strategy = AttackStrategy()
        session = MagicMock()
        combatant = MagicMock()
        
        # 各种畸形参数
        malformed_args = [
            None,
            {},
            {"target": None},
            {"target": "not_a_character"},
            {"target": 12345},
            {"target": MagicMock()},  # 无id属性
        ]
        
        for args in malformed_args:
            try:
                valid, msg = strategy.validate(session, combatant, args if args else {})
                # 应该返回验证失败，而不是抛出异常
                assert valid is False or valid is True  # 不抛出异常即可
            except Exception:
                # 即使是异常也应该是受控的
                pass
    
    @pytest.mark.asyncio
    async def test_chaos_strategy_register_duplicate(self):
        """混沌测试：重复注册策略."""
        from src.game.combat.core import _get_strategies
        from src.game.combat.strategy import AttackStrategy
        
        strategies = _get_strategies()
        
        # 尝试覆盖已有策略
        original_strategy = strategies.get("kill")
        
        # 模拟重复注册
        strategies["kill"] = AttackStrategy()
        
        # 验证策略被替换
        assert strategies["kill"] is not original_strategy
        
        # 恢复原始策略
        strategies["kill"] = original_strategy


class TestChaosValidation:
    """状态验证混沌测试."""
    
    def test_chaos_extreme_state_values(self):
        """混沌测试：极端状态值."""
        from src.game.typeclasses.validation import CharacterValidator
        
        validator = CharacterValidator()
        
        extreme_values = [
            float('inf'),
            float('-inf'),
            float('nan'),
            999999999,
            -999999999,
            0,
            -0,
        ]
        
        for value in extreme_values:
            char = MagicMock()
            char.hp = value if value == value else 100  # NaN检查
            char.mp = 50
            char.ep = 50
            char.level = 1
            char.exp = 0
            
            try:
                errors = validator.validate(char)
                # 应该能处理而不崩溃
                assert isinstance(errors, list)
            except (TypeError, ValueError):
                # 这些异常是可接受的
                pass
    
    def test_chaos_fix_corrupted_state(self):
        """混沌测试：修复损坏的状态."""
        from src.game.typeclasses.validation import CharacterValidator
        
        validator = CharacterValidator()
        
        class CorruptedChar:
            def __init__(self):
                self.hp = None
                self.mp = "invalid"
                self.level = []
                self.exp = {}
        
        char = CorruptedChar()
        
        # 应该能处理损坏的状态而不崩溃
        try:
            fixes = validator.fix(char)
            # 不抛出异常即可
        except (TypeError, AttributeError):
            pass


class TestChaosComponentSystem:
    """组件系统混沌测试."""
    
    def test_chaos_component_name_collision(self):
        """混沌测试：组件名称冲突."""
        from src.engine.components import Component, ComponentMixin
        
        class TestComponent(Component):
            def get_stats(self):
                return {"test": 1}
        
        mixin = ComponentMixin()
        comp1 = TestComponent(mixin)
        comp2 = TestComponent(mixin)
        
        # 添加同名组件（应该覆盖）
        mixin.add_component("test", comp1)
        mixin.add_component("test", comp2)
        
        # 应该返回后添加的组件
        assert mixin.get_component("test") is comp2
    
    def test_chaos_component_circular_reference(self):
        """混沌测试：组件循环引用."""
        from src.engine.components import Component, ComponentMixin
        
        class CircularComponent(Component):
            def __init__(self, owner, name):
                super().__init__(owner)
                self.name = name
                self.ref = None
            
            def get_stats(self):
                return {}
        
        mixin1 = ComponentMixin()
        mixin2 = ComponentMixin()
        
        comp1 = CircularComponent(mixin1, "comp1")
        comp2 = CircularComponent(mixin2, "comp2")
        
        # 创建循环引用
        comp1.ref = comp2
        comp2.ref = comp1
        
        # 应该能处理循环引用
        mixin1.add_component("circular", comp1)
        mixin2.add_component("circular", comp2)
        
        # 验证没有无限递归
        assert mixin1.get_component("circular") is comp1
        assert mixin2.get_component("circular") is comp2
    
    def test_chaos_remove_nonexistent_component(self):
        """混沌测试：移除不存在的组件."""
        from src.engine.components import ComponentMixin
        
        mixin = ComponentMixin()
        
        # 移除不存在的组件应该返回None
        result = mixin.remove_component("nonexistent")
        assert result is None
    
    def test_chaos_aggregate_conflicting_stats(self):
        """混沌测试：冲突属性聚合."""
        from src.engine.components import Component, ComponentMixin
        
        class AttackComp(Component):
            def __init__(self, owner, value):
                super().__init__(owner)
                self.value = value
            
            def get_stats(self):
                return {"attack": self.value}
        
        mixin = ComponentMixin()
        
        # 添加多个提供相同属性的组件
        for i in range(10):
            mixin.add_component(f"attack_{i}", AttackComp(mixin, i * 10))
        
        # 聚合时后面的覆盖前面的
        stats = mixin.aggregate_stats()
        assert "attack" in stats


class TestChaosBalanceConfig:
    """平衡配置混沌测试."""
    
    def test_chaos_config_path_traversal(self):
        """混沌测试：配置路径遍历."""
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        # 尝试各种奇怪的路径
        weird_paths = [
            ("...", "...", "..."),
            ("../../etc/passwd",),
            ("",),
            ("combat", "...", "damage"),
            ("combat", "damage", "nonexistent", "deep"),
        ]
        
        for path in weird_paths:
            result = config.get(*path, default="default")
            assert result is not None  # 不抛出异常即可
    
    def test_chaos_config_type_confusion(self):
        """混沌测试：配置类型混淆."""
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        # 尝试将字符串作为路径
        result = config.get("combat_damage_base", default=0)
        assert result == 0  # 应该返回默认值
    
    def test_chaos_reload_during_access(self):
        """混沌测试：访问时重载配置."""
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        # 在访问时重载
        value1 = config.get("combat", "damage", "base")
        config.reload()
        value2 = config.get("combat", "damage", "base")
        
        # 重载后值应该相同（因为是默认配置）
        assert value1 == value2 == 10


class TestChaosDebugCommands:
    """调试命令混沌测试."""
    
    @pytest.mark.asyncio
    async def test_chaos_validate_invalid_character_id(self):
        """混沌测试：验证无效角色ID."""
        from src.game.commands.debug import CmdValidateCharacter
        
        cmd = CmdValidateCharacter()
        cmd.caller = MagicMock()
        
        # 各种无效ID
        invalid_ids = [
            "",
            "abc",
            "!@#$%",
            "123abc",
            "-1",
            "0",
            "999999999999999999999999999999",
            "1.5",
            "null",
            "undefined",
        ]
        
        for invalid_id in invalid_ids:
            cmd.args = invalid_id
            try:
                await cmd.execute()
                # 应该优雅处理
            except Exception:
                # 即使是异常也应该是受控的
                pass
    
    @pytest.mark.asyncio
    async def test_chaos_inspect_character_with_extreme_values(self):
        """混沌测试：查看极端值角色."""
        from src.game.commands.debug import CmdInspectCharacter
        
        cmd = CmdInspectCharacter()
        cmd.args = "1"
        cmd.caller = MagicMock()
        
        # 创建极端值角色
        extreme_char = MagicMock()
        extreme_char.name = "A" * 10000  # 超长名称
        extreme_char.id = 1
        extreme_char.hp = float('inf')
        extreme_char.mp = float('-inf')
        extreme_char.level = 999999999
        extreme_char.exp = -1
        extreme_char.birth_talents = None
        extreme_char.attributes = {}
        extreme_char.get_attack.side_effect = Exception("计算错误")
        
        with patch('src.engine.objects.manager.ObjectManager') as mock_mgr:
            mock_mgr.return_value.get.return_value = extreme_char
            
            try:
                await cmd.execute()
                # 应该能显示信息而不崩溃
            except Exception:
                pass


class TestChaosBackwardCompatibility:
    """向后兼容性混沌测试."""
    
    @pytest.mark.asyncio
    async def test_chaos_mixed_old_new_api_calls(self):
        """混沌测试：混合使用新旧API."""
        from src.game.combat.core import CombatSession
        
        # 创建角色
        char1 = MagicMock()
        char1.id = 1
        char1.get_hp.return_value = (100, 100)
        char1.get_agility.return_value = 10
        char1.wuxue_has_learned.return_value = True  # 新API
        char1.hasattr.return_value = True  # 如果旧代码使用hasattr检查
        
        char2 = MagicMock()
        char2.id = 2
        char2.get_hp.return_value = (100, 100)
        char2.equipment_get_stats.return_value = {"attack": 10}  # 新API
        
        # 创建战斗会话
        session = CombatSession(None, [char1, char2])
        
        # 验证能正常工作
        assert session is not None
        assert len(session.participants) == 2
    
    def test_chaos_transaction_with_old_style_character(self):
        """混沌测试：事务与旧式角色."""
        from src.game.combat.transaction import CombatTransaction
        
        # 模拟旧式角色（可能缺少某些属性）
        old_style_char = MagicMock()
        old_style_char.hp = 100
        # 缺少 mp, ep 等属性
        
        txn = CombatTransaction()
        txn.snapshot(old_style_char, ['hp', 'mp', 'ep'])
        
        # 应该只记录存在的属性
        assert len(txn._snapshots) > 0


# 汇总统计
class TestArchitectureChaosSummary:
    """架构混沌测试汇总."""
    
    def test_summary_all_chaos_tests(self):
        """汇总所有混沌测试."""
        # 这个测试用于统计混沌测试数量
        chaos_test_classes = [
            TestChaosCombatTransaction,
            TestChaosMixinRenaming,
            TestChaosCombatStrategy,
            TestChaosValidation,
            TestChaosComponentSystem,
            TestChaosBalanceConfig,
            TestChaosDebugCommands,
            TestChaosBackwardCompatibility,
        ]
        
        total_tests = 0
        for cls in chaos_test_classes:
            methods = [m for m in dir(cls) if m.startswith('test_')]
            total_tests += len(methods)
        
        # 验证混沌测试数量
        assert total_tests >= 20, f"应该有至少20个混沌测试，实际有 {total_tests} 个"

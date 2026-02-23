"""武学注册表单元测试.

测试TD-017: 武学缓存
"""

import pytest
from unittest.mock import MagicMock

from src.game.data.wuxue_registry import (
    WuxueRegistry,
    get_wuxue_registry,
    register_kungfu,
    get_kungfu,
    reset_wuxue_registry,
)
from src.game.typeclasses.wuxue import Kungfu, WuxueType, Move


class TestWuxueRegistry:
    """测试武学注册表."""
    
    def setup_method(self):
        """每个测试前重置."""
        reset_wuxue_registry()
    
    def teardown_method(self):
        """每个测试后清理."""
        reset_wuxue_registry()
    
    def test_singleton(self):
        """测试单例模式."""
        reg1 = get_wuxue_registry()
        reg2 = get_wuxue_registry()
        assert reg1 is reg2
    
    def test_register_and_get(self):
        """测试注册和获取."""
        kungfu = Kungfu(
            key="shaolin_jian",
            name="少林剑法",
            menpai="少林",
            wuxue_type=WuxueType.JIAN
        )
        
        registry = get_wuxue_registry()
        registry.register(kungfu)
        
        retrieved = registry.get("shaolin_jian")
        assert retrieved is kungfu
        assert retrieved.name == "少林剑法"
    
    def test_get_nonexistent(self):
        """测试获取不存在的武功."""
        registry = get_wuxue_registry()
        assert registry.get("nonexistent") is None
    
    def test_has(self):
        """测试检查存在."""
        kungfu = Kungfu(
            key="test_kungfu",
            name="测试武功",
            menpai="测试门派",
            wuxue_type=WuxueType.QUAN
        )
        
        registry = get_wuxue_registry()
        assert not registry.has("test_kungfu")
        
        registry.register(kungfu)
        assert registry.has("test_kungfu")
    
    def test_get_by_menpai(self):
        """测试按门派获取."""
        registry = get_wuxue_registry()
        
        # 注册少林武功
        shaolin1 = Kungfu("shaolin_1", "少林拳", "少林", WuxueType.QUAN)
        shaolin2 = Kungfu("shaolin_2", "少林剑", "少林", WuxueType.JIAN)
        wudang1 = Kungfu("wudang_1", "武当剑", "武当", WuxueType.JIAN)
        
        registry.register(shaolin1)
        registry.register(shaolin2)
        registry.register(wudang1)
        
        shaolin_kungfu = registry.get_by_menpai("少林")
        assert len(shaolin_kungfu) == 2
        assert all(k.menpai == "少林" for k in shaolin_kungfu)
    
    def test_get_by_type(self):
        """测试按类型获取."""
        registry = get_wuxue_registry()
        
        quan = Kungfu("quan_1", "拳法", "门派1", WuxueType.QUAN)
        jian = Kungfu("jian_1", "剑法", "门派2", WuxueType.JIAN)
        dao = Kungfu("dao_1", "刀法", "门派3", WuxueType.DAO)
        
        registry.register(quan)
        registry.register(jian)
        registry.register(dao)
        
        jian_kungfu = registry.get_by_type(WuxueType.JIAN)
        assert len(jian_kungfu) == 1
        assert jian_kungfu[0].key == "jian_1"
    
    def test_get_all(self):
        """测试获取所有."""
        registry = get_wuxue_registry()
        
        assert len(registry.get_all()) == 0
        
        registry.register(Kungfu("k1", "武功1", "门派", WuxueType.QUAN))
        registry.register(Kungfu("k2", "武功2", "门派", WuxueType.JIAN))
        
        all_kungfu = registry.get_all()
        assert len(all_kungfu) == 2
    
    def test_clear(self):
        """测试清空."""
        registry = get_wuxue_registry()
        registry.register(Kungfu("k1", "武功1", "门派", WuxueType.QUAN))
        
        assert len(registry.get_all()) == 1
        registry.clear()
        assert len(registry.get_all()) == 0
    
    def test_duplicate_register(self):
        """测试重复注册（应忽略）."""
        registry = get_wuxue_registry()
        
        k1 = Kungfu("same_key", "武功1", "门派", WuxueType.QUAN)
        k2 = Kungfu("same_key", "武功2", "门派", WuxueType.JIAN)
        
        registry.register(k1)
        registry.register(k2)  # 重复key
        
        # 后注册的应该覆盖
        retrieved = registry.get("same_key")
        assert retrieved.name == "武功2"


class TestConvenienceFunctions:
    """测试便捷函数."""
    
    def setup_method(self):
        """每个测试前重置."""
        reset_wuxue_registry()
    
    def teardown_method(self):
        """每个测试后清理."""
        reset_wuxue_registry()
    
    def test_register_kungfu(self):
        """测试register_kungfu函数."""
        kungfu = Kungfu("test", "测试", "门派", WuxueType.QUAN)
        register_kungfu(kungfu)
        
        assert get_kungfu("test") is kungfu
    
    def test_get_kungfu_none(self):
        """测试get_kungfu返回None."""
        assert get_kungfu("nonexistent") is None


class TestCharacterWuxueMixin:
    """测试CharacterWuxueMixin的get_available_moves."""
    
    def setup_method(self):
        """每个测试前重置注册表."""
        reset_wuxue_registry()
    
    def teardown_method(self):
        """每个测试后清理."""
        reset_wuxue_registry()
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin
        
        char = MagicMock(spec=CharacterWuxueMixin)
        char.learned_wuxue = {
            "shaolin_jian": {
                "level": 1,
                "moves": {"move1": 10, "move2": 20}
            },
            "wudang_jian": {
                "level": 2,
                "moves": {"move3": 30}
            }
        }
        
        # 绑定真实方法
        char.get_available_moves = lambda: CharacterWuxueMixin.get_available_moves(char)
        
        return char
    
    def test_get_available_moves(self, mock_character):
        """测试获取可用招式."""
        # 注册武功
        shaolin_jian = Kungfu(
            key="shaolin_jian",
            name="少林剑法",
            menpai="少林",
            wuxue_type=WuxueType.JIAN,
            moves=[
                Move("move1", "招式1", WuxueType.JIAN),
                Move("move2", "招式2", WuxueType.JIAN),
            ]
        )
        wudang_jian = Kungfu(
            key="wudang_jian",
            name="武当剑法",
            menpai="武当",
            wuxue_type=WuxueType.JIAN,
            moves=[
                Move("move3", "招式3", WuxueType.JIAN),
            ]
        )
        
        register_kungfu(shaolin_jian)
        register_kungfu(wudang_jian)
        
        # 获取可用招式
        moves = mock_character.get_available_moves()
        
        assert len(moves) == 3  # 2个少林招式 + 1个武当招式
        
        # 验证返回格式 (Kungfu, Move)
        for kungfu, move in moves:
            assert isinstance(kungfu, Kungfu)
            assert isinstance(move, Move)
    
    def test_get_available_moves_missing_kungfu(self, mock_character):
        """测试武功未注册的情况."""
        # 只注册一个武功
        shaolin_jian = Kungfu(
            key="shaolin_jian",
            name="少林剑法",
            menpai="少林",
            wuxue_type=WuxueType.JIAN,
            moves=[Move("move1", "招式1", WuxueType.JIAN)]
        )
        register_kungfu(shaolin_jian)
        # 不注册 wudang_jian
        
        moves = mock_character.get_available_moves()
        
        # 只返回已注册武功的招式
        assert len(moves) == 1
    
    def test_get_available_moves_empty(self):
        """测试无学习武功."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin
        
        char = MagicMock(spec=CharacterWuxueMixin)
        char.learned_wuxue = {}
        char.get_available_moves = lambda: CharacterWuxueMixin.get_available_moves(char)
        
        moves = char.get_available_moves()
        assert len(moves) == 0

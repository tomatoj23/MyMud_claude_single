"""富文本格式化测试."""

from __future__ import annotations

from src.gui.utils import RichTextFormatter


class TestRichTextFormatter:
    """富文本格式化器测试."""

    def test_format_message_basic(self):
        """测试基本消息格式化."""
        result = RichTextFormatter.format_message("info", "Hello World")
        assert "Hello World" in result
        assert "span" in result
        assert "color" in result

    def test_format_message_escape_html(self):
        """测试HTML转义."""
        result = RichTextFormatter.format_message("info", "<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_format_bold(self):
        """测试粗体格式."""
        result = RichTextFormatter._process_inline_formats("**bold text**")
        assert "<strong>bold text</strong>" in result

    def test_format_italic(self):
        """测试斜体格式."""
        result = RichTextFormatter._process_inline_formats("*italic text*")
        assert "<em>italic text</em>" in result

    def test_format_code(self):
        """测试代码格式."""
        result = RichTextFormatter._process_inline_formats("`code block`")
        assert "<code" in result
        assert "code block" in result

    def test_format_color(self):
        """测试颜色标记."""
        result = RichTextFormatter._process_inline_formats("{red:red text}")
        assert "#cc0000" in result
        assert "red text" in result

    def test_format_hp_bar(self):
        """测试HP条格式化."""
        result = RichTextFormatter.format_hp_bar(50, 100, 20)
        assert "50/100" in result
        assert "50%" in result
        assert "█" in result

    def test_format_hp_bar_low(self):
        """测试低HP条."""
        result = RichTextFormatter.format_hp_bar(20, 100, 20)
        assert "#cc0000" in result  # 红色

    def test_format_hp_bar_high(self):
        """测试高HP条."""
        result = RichTextFormatter.format_hp_bar(80, 100, 20)
        assert "#00cc00" in result  # 绿色

    def test_format_table(self):
        """测试表格格式化."""
        headers = ["Name", "Level", "HP"]
        rows = [
            ["Player1", 10, 100],
            ["Player2", 20, 200],
        ]
        result = RichTextFormatter.format_table(headers, rows)
        assert "<table" in result
        assert "Name" in result
        assert "Player1" in result

    def test_format_list_unordered(self):
        """测试无序列表."""
        items = ["Item 1", "Item 2", "Item 3"]
        result = RichTextFormatter.format_list(items, ordered=False)
        assert "<ul" in result
        assert "Item 1" in result

    def test_format_list_ordered(self):
        """测试有序列表."""
        items = ["First", "Second", "Third"]
        result = RichTextFormatter.format_list(items, ordered=True)
        assert "<ol" in result
        assert "First" in result

    def test_format_divider(self):
        """测试分隔线."""
        result = RichTextFormatter.format_divider("─", 30)
        assert "─" * 30 in result

    def test_format_box(self):
        """测试文本框."""
        result = RichTextFormatter.format_box("Content", "Title")
        assert "Content" in result
        assert "Title" in result
        assert "border" in result

    def test_format_box_no_title(self):
        """测试无标题文本框."""
        result = RichTextFormatter.format_box("Content")
        assert "Content" in result
        assert "border" in result

    def test_message_colors(self):
        """测试消息类型颜色."""
        assert "error" in RichTextFormatter.MESSAGE_COLORS
        assert "combat" in RichTextFormatter.MESSAGE_COLORS
        assert "dialogue" in RichTextFormatter.MESSAGE_COLORS

    def test_color_map(self):
        """测试颜色映射."""
        assert "red" in RichTextFormatter.COLOR_MAP
        assert "green" in RichTextFormatter.COLOR_MAP
        assert "blue" in RichTextFormatter.COLOR_MAP

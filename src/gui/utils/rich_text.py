"""富文本格式化工具."""

from __future__ import annotations

import html
import re
from typing import Any


class RichTextFormatter:
    """富文本格式化器.

    支持多种文本格式化功能：
    - 颜色标记
    - 粗体/斜体
    - 链接
    - 代码块
    """

    # 颜色映射
    COLOR_MAP = {
        "red": "#cc0000",
        "green": "#00cc00",
        "blue": "#0066cc",
        "yellow": "#cccc00",
        "cyan": "#00cccc",
        "magenta": "#cc00cc",
        "white": "#ffffff",
        "gray": "#666666",
        "orange": "#ff8800",
        "purple": "#8800cc",
    }

    # 消息类型颜色
    MESSAGE_COLORS = {
        "error": "#cc0000",
        "combat": "#ff4444",
        "dialogue": "#0066cc",
        "notify": "#00aa00",
        "system": "#888888",
        "info": "#cccccc",
        "prompt": "#ffffff",
        "warning": "#ffaa00",
        "success": "#00cc00",
    }

    @staticmethod
    def format_message(msg_type: str, content: str) -> str:
        """格式化消息.

        Args:
            msg_type: 消息类型
            content: 消息内容

        Returns:
            HTML格式化的消息
        """
        # 转义HTML特殊字符
        safe_content = html.escape(content)

        # 处理内联格式标记
        formatted = RichTextFormatter._process_inline_formats(safe_content)

        # 应用消息类型颜色
        color = RichTextFormatter.MESSAGE_COLORS.get(msg_type, "#cccccc")
        return f'<span style="color: {color};">{formatted}</span>'

    @staticmethod
    def _process_inline_formats(text: str) -> str:
        """处理内联格式标记.

        支持的格式：
        - **粗体**
        - *斜体*
        - `代码`
        - [链接文本](url)
        - {color:文本}

        Args:
            text: 原始文本

        Returns:
            处理后的HTML
        """
        # 粗体: **text**
        text = re.sub(
            r"\*\*(.+?)\*\*",
            r'<strong>\1</strong>',
            text
        )

        # 斜体: *text*
        text = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            r'<em>\1</em>',
            text
        )

        # 代码: `text`
        text = re.sub(
            r"`(.+?)`",
            r'<code style="background-color: #2d2d2d; padding: 2px 4px; border-radius: 3px;">\1</code>',
            text
        )

        # 颜色标记: {color:text}
        def replace_color(match):
            color_name = match.group(1)
            content = match.group(2)
            color = RichTextFormatter.COLOR_MAP.get(color_name, "#cccccc")
            return f'<span style="color: {color};">{content}</span>'

        text = re.sub(r"\{(\w+):(.+?)\}", replace_color, text)

        return text

    @staticmethod
    def format_hp_bar(current: int, maximum: int, width: int = 20) -> str:
        """格式化HP条.

        Args:
            current: 当前值
            maximum: 最大值
            width: 条宽度

        Returns:
            HTML格式的HP条
        """
        if maximum <= 0:
            percentage = 0
        else:
            percentage = min(100, int(current / maximum * 100))

        filled = int(width * percentage / 100)
        empty = width - filled

        # 根据百分比选择颜色
        if percentage > 60:
            color = "#00cc00"  # 绿色
        elif percentage > 30:
            color = "#ffaa00"  # 橙色
        else:
            color = "#cc0000"  # 红色

        bar = (
            f'<span style="color: {color};">{"█" * filled}</span>'
            f'<span style="color: #333333;">{"░" * empty}</span>'
        )

        return f'{bar} {current}/{maximum} ({percentage}%)'

    @staticmethod
    def format_table(headers: list[str], rows: list[list[Any]]) -> str:
        """格式化表格.

        Args:
            headers: 表头
            rows: 数据行

        Returns:
            HTML表格
        """
        html_parts = ['<table style="border-collapse: collapse; margin: 10px 0;">']

        # 表头
        html_parts.append('<thead><tr>')
        for header in headers:
            html_parts.append(
                f'<th style="border: 1px solid #555; padding: 5px 10px; '
                f'background-color: #2d2d2d;">{html.escape(str(header))}</th>'
            )
        html_parts.append('</tr></thead>')

        # 数据行
        html_parts.append('<tbody>')
        for row in rows:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(
                    f'<td style="border: 1px solid #555; padding: 5px 10px;">'
                    f'{html.escape(str(cell))}</td>'
                )
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

        html_parts.append('</table>')
        return ''.join(html_parts)

    @staticmethod
    def format_list(items: list[str], ordered: bool = False) -> str:
        """格式化列表.

        Args:
            items: 列表项
            ordered: 是否有序列表

        Returns:
            HTML列表
        """
        tag = 'ol' if ordered else 'ul'
        html_parts = [f'<{tag} style="margin: 5px 0; padding-left: 20px;">']

        for item in items:
            html_parts.append(f'<li>{html.escape(item)}</li>')

        html_parts.append(f'</{tag}>')
        return ''.join(html_parts)

    @staticmethod
    def format_divider(char: str = "─", length: int = 50) -> str:
        """格式化分隔线.

        Args:
            char: 分隔字符
            length: 长度

        Returns:
            HTML分隔线
        """
        return f'<div style="color: #555555; margin: 5px 0;">{char * length}</div>'

    @staticmethod
    def format_box(content: str, title: str = "") -> str:
        """格式化文本框.

        Args:
            content: 内容
            title: 标题

        Returns:
            HTML文本框
        """
        title_html = ""
        if title:
            title_html = (
                f'<div style="background-color: #2d2d2d; padding: 5px 10px; '
                f'font-weight: bold; border-bottom: 1px solid #555;">'
                f'{html.escape(title)}</div>'
            )

        return (
            f'<div style="border: 1px solid #555; margin: 10px 0; border-radius: 4px;">'
            f'{title_html}'
            f'<div style="padding: 10px;">{html.escape(content)}</div>'
            f'</div>'
        )

"""默认命令实现.

提供基础的游戏命令。
"""

from __future__ import annotations

from src.engine.commands.command import Command, CommandResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CmdLook(Command):
    """查看命令.

    用法: look [目标]
           看 [目标]
           l [目标]
    """

    key = "look"
    aliases = ["l", "看"]
    locks = ""
    help_category = "general"
    help_text = "查看周围环境或指定目标。"

    async def execute(self) -> CommandResult:
        """执行查看."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        if not self.args:
            # 查看当前位置
            location = self.caller.location
            if location:
                desc = location.at_desc(self.caller)
                self.msg(desc)

                # 显示位置内容
                contents = [
                    getattr(obj, 'name', None) or obj.key
                    for obj in location.contents
                    if obj != self.caller
                ]
                if contents:
                    self.msg(f"\n这里还有: {', '.join(contents)}")
            else:
                self.msg("你在虚空中漂浮...")

            return CommandResult(True)
        else:
            # 查看指定目标
            target = self.search(
                self.args,
                nofound_string=f"这里没有 '{self.args}'。",
                multimatch_string="你想看哪个?",
            )

            if target:
                desc = target.at_desc(self.caller)
                self.msg(desc)
                return CommandResult(True)

            return CommandResult(False)


class CmdMove(Command):
    """移动命令.

    用法: goto <目标>
           enter <目标>
           go <目标>
    """

    key = "goto"
    aliases = ["go", "enter", "去", "进入"]
    locks = ""
    help_category = "general"
    help_text = "移动到指定目标位置。"

    async def execute(self) -> CommandResult:
        """执行移动."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        if not self.args:
            self.msg("你要去哪里?")
            return CommandResult(False)

        # 搜索目标
        target = self.search(
            self.args,
            nofound_string=f"这里没有 '{self.args}'。",
            multimatch_string="你想去哪个?",
        )

        if not target:
            return CommandResult(False)

        # 执行移动
        old_location = self.caller.location
        self.caller.location = target

        if old_location:
            self.msg(f"你离开了 {old_location.key}。")

        self.msg(f"你来到了 {target.key}。")

        # 触发查看
        look_cmd = CmdLook()
        look_cmd.caller = self.caller
        look_cmd.args = ""
        await look_cmd.execute()

        return CommandResult(True)


class CmdInventory(Command):
    """背包命令.

    用法: inventory
           inv
           i
           背包
    """

    key = "inventory"
    aliases = ["inv", "i", "背包", "物品"]
    locks = ""
    help_category = "general"
    help_text = "查看你携带的物品。"

    async def execute(self) -> CommandResult:
        """执行背包查看."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        # 获取自己包含的物品
        items = self.caller.contents

        if not items:
            self.msg("你的背包是空的。")
        else:
            item_names = [f"  {item.key}" for item in items]
            self.msg("你的背包里有:\n" + "\n".join(item_names))

        return CommandResult(True)


class CmdCreate(Command):
    """创建命令.

    用法: create <名称> [<类型>]
           create 箱子
           create 宝箱 src.game.objects.Container
    """

    key = "create"
    aliases = ["cre", "创建", "新建"]
    locks = "perm:builder"  # 需要builder权限
    help_category = "building"
    help_text = "创建一个新的对象。"

    async def execute(self) -> CommandResult:
        """执行创建."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        if not self.args:
            self.msg("你要创建什么?\n用法: create <名称> [<类型>]")
            return CommandResult(False)

        # 解析参数
        parts = self.args.split(None, 1)
        name = parts[0]
        typeclass = parts[1] if len(parts) > 1 else "src.engine.core.typeclass.TypeclassBase"

        # 创建对象
        try:
            from src.engine.core.typeclass import TypeclassLoader

            # 验证类型类
            TypeclassLoader.load(typeclass)

            # 创建对象
            obj = await self.caller._manager.create(
                typeclass_path=typeclass,
                key=name,
                location=self.caller.location,
            )

            self.msg(f"你创建了: {obj.key} (id={obj.id})")
            return CommandResult(True, data={"object": obj})

        except Exception as e:
            logger.exception("创建对象失败")
            self.msg(f"创建失败: {e}")
            return CommandResult(False, str(e))


class CmdDestroy(Command):
    """删除命令.

    用法: destroy <名称>
           destroy 箱子
    """

    key = "destroy"
    aliases = ["del", "delete", "删除", "销毁"]
    locks = "perm:builder"  # 需要builder权限
    help_category = "building"
    help_text = "删除一个对象。"

    async def execute(self) -> CommandResult:
        """执行删除."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        if not self.args:
            self.msg("你要删除什么?\n用法: destroy <名称>")
            return CommandResult(False)

        # 搜索目标
        target = self.search(
            self.args,
            nofound_string=f"这里没有 '{self.args}'。",
            multimatch_string="你想删除哪个?",
        )

        if not target:
            return CommandResult(False)

        # 执行删除
        name = target.key
        success = await self.caller._manager.delete(target)

        if success:
            self.msg(f"你删除了: {name}")
            return CommandResult(True)
        else:
            self.msg(f"删除失败: {name}")
            return CommandResult(False)


class CmdHelp(Command):
    """帮助命令.

    用法: help [命令]
           help
           help look
    """

    key = "help"
    aliases = ["h", "?", "帮助"]
    locks = ""
    help_category = "general"
    help_text = "查看游戏帮助。"

    async def execute(self) -> CommandResult:
        """执行帮助."""
        if not self.caller:
            return CommandResult(False, "调用者未设置")

        if not self.args:
            # 显示帮助概览
            self.msg(
                "=== 游戏帮助 ===\n\n"
                "基础命令:\n"
                "  look/l/看 - 查看周围环境\n"
                "  goto/go/去 <目标> - 移动\n"
                "  inventory/inv/i/背包 - 查看背包\n"
                "  help/? - 查看帮助\n\n"
                "建筑命令:\n"
                "  create/cre <名称> [<类型>] - 创建对象\n"
                "  destroy/del <名称> - 删除对象\n\n"
                "输入 'help <命令>' 查看详细帮助。"
            )
            return CommandResult(True)

        # 显示指定命令帮助
        # 需要访问命令集合
        # 简化实现：直接提示
        self.msg(f"命令 '{self.args}' 的详细帮助暂未实现。")
        return CommandResult(True)

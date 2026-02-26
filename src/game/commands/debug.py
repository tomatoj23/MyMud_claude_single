"""调试命令.

提供开发者调试工具。
"""

from __future__ import annotations

from src.engine.commands.command import Command


class CmdValidateCharacter(Command):
    """验证角色状态命令.
    
    用法: @validate_character <角色ID>
    别名: @vc
    """
    key = "@validate_character"
    aliases = ["@vc"]
    locks = "perm(Admin)"
    
    async def execute(self):
        if not self.args:
            self.caller.msg("用法: @validate_character <角色ID>")
            return
        
        try:
            char_id = int(self.args)
        except ValueError:
            self.caller.msg("角色ID必须是数字")
            return
        
        # 获取角色
        from src.engine.objects.manager import ObjectManager
        manager = ObjectManager()
        character = manager.get(char_id)
        
        if not character:
            self.caller.msg(f"找不到角色: {char_id}")
            return
        
        # 验证状态
        errors = character.validate_state()
        
        if not errors:
            self.caller.msg(f"角色 {character.name} 状态正常")
        else:
            self.caller.msg(f"角色 {character.name} 状态异常:")
            for error in errors:
                self.caller.msg(f"  - {error}")
            
            # 询问是否修复
            fixes = character.fix_state()
            if fixes:
                self.caller.msg("已自动修复:")
                for fix in fixes:
                    self.caller.msg(f"  - {fix}")


class CmdInspectCharacter(Command):
    """查看角色详细信息命令.
    
    用法: @inspect_character <角色ID>
    别名: @ic
    """
    key = "@inspect_character"
    aliases = ["@ic"]
    locks = "perm(Admin)"
    
    async def execute(self):
        if not self.args:
            self.caller.msg("用法: @inspect_character <角色ID>")
            return
        
        try:
            char_id = int(self.args)
        except ValueError:
            self.caller.msg("角色ID必须是数字")
            return
        
        # 获取角色
        from src.engine.objects.manager import ObjectManager
        manager = ObjectManager()
        character = manager.get(char_id)
        
        if not character:
            self.caller.msg(f"找不到角色: {char_id}")
            return
        
        # 显示详细信息
        self.caller.msg(f"=== 角色详情: {character.name} ===")
        self.caller.msg(f"ID: {character.id}")
        self.caller.msg(f"Key: {character.key}")
        
        # 状态
        if hasattr(character, 'hp'):
            self.caller.msg(f"HP: {character.hp}/{character.max_hp}")
        if hasattr(character, 'mp'):
            self.caller.msg(f"MP: {character.mp}/{character.max_mp}")
        if hasattr(character, 'ep'):
            self.caller.msg(f"EP: {character.ep}/{character.max_ep}")
        
        # 等级
        if hasattr(character, 'level'):
            self.caller.msg(f"等级: {character.level}")
        if hasattr(character, 'exp'):
            self.caller.msg(f"经验: {character.exp}")
        
        # 先天资质
        if hasattr(character, 'birth_talents'):
            talents = character.birth_talents
            self.caller.msg(f"根骨: {talents.get('gengu', 0)}")
            self.caller.msg(f"悟性: {talents.get('wuxing', 0)}")
            self.caller.msg(f"福缘: {talents.get('fuyuan', 0)}")
            self.caller.msg(f"容貌: {talents.get('rongmao', 0)}")
        
        # 后天属性
        if hasattr(character, 'attributes'):
            attrs = character.attributes
            self.caller.msg(f"臂力: {attrs.get('strength', 0)}")
            self.caller.msg(f"身法: {attrs.get('agility', 0)}")
            self.caller.msg(f"体质: {attrs.get('constitution', 0)}")
            self.caller.msg(f"精神: {attrs.get('spirit', 0)}")
        
        # 战斗属性
        if hasattr(character, 'get_attack'):
            self.caller.msg(f"攻击力: {character.get_attack()}")
        if hasattr(character, 'get_defense'):
            self.caller.msg(f"防御力: {character.get_defense()}")
        if hasattr(character, 'get_agility'):
            self.caller.msg(f"敏捷: {character.get_agility()}")
        
        # 装备
        if hasattr(character, 'equipment_slots'):
            self.caller.msg(f"已装备: {len(character.equipment_slots)} 个槽位")
        
        # 武学
        if hasattr(character, 'wuxue_learned'):
            learned = character.wuxue_learned
            self.caller.msg(f"已学武功: {len(learned)} 门")
        
        # 状态验证
        if hasattr(character, 'is_state_valid'):
            valid = character.is_state_valid()
            self.caller.msg(f"状态有效: {'是' if valid else '否'}")


class CmdValidateAll(Command):
    """验证所有角色状态命令.
    
    用法: @validate_all
    """
    key = "@validate_all"
    locks = "perm(Admin)"
    
    async def execute(self):
        from src.engine.objects.manager import ObjectManager
        
        manager = ObjectManager()
        characters = [
            obj for obj in manager._cache.values()
            if hasattr(obj, 'validate_state')
        ]
        
        invalid_count = 0
        fixed_count = 0
        
        self.caller.msg(f"开始验证 {len(characters)} 个角色...")
        
        for char in characters:
            errors = char.validate_state()
            if errors:
                invalid_count += 1
                self.caller.msg(f"{char.name}: {len(errors)} 个错误")
                
                fixes = char.fix_state()
                if fixes:
                    fixed_count += len(fixes)
        
        if invalid_count == 0:
            self.caller.msg("所有角色状态正常")
        else:
            self.caller.msg(f"发现 {invalid_count} 个角色状态异常，已修复 {fixed_count} 个问题")


class CmdBalanceConfig(Command):
    """查看游戏平衡配置命令.
    
    用法: @balance_config [路径]
    示例: @balance_config combat damage base
    """
    key = "@balance_config"
    locks = "perm(Admin)"
    
    async def execute(self):
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        
        if not self.args:
            # 显示所有配置
            all_config = config.get_all()
            self._show_config(all_config)
            return
        
        # 显示特定路径
        keys = self.args.split()
        value = config.get(*keys)
        
        if value is None:
            self.caller.msg(f"配置项不存在: {self.args}")
            return
        
        if isinstance(value, dict):
            self._show_config(value, indent=0)
        else:
            self.caller.msg(f"{'.'.join(keys)} = {value}")
    
    def _show_config(self, config: dict, indent: int = 0):
        """递归显示配置."""
        prefix = "  " * indent
        for key, value in config.items():
            if isinstance(value, dict):
                self.caller.msg(f"{prefix}{key}:")
                self._show_config(value, indent + 1)
            elif isinstance(value, list):
                self.caller.msg(f"{prefix}{key}: {value}")
            else:
                self.caller.msg(f"{prefix}{key}: {value}")


class CmdReloadConfig(Command):
    """重新加载配置文件命令.
    
    用法: @reload_config
    """
    key = "@reload_config"
    locks = "perm(Admin)"
    
    async def execute(self):
        from src.utils.config_loader import get_balance_config
        
        config = get_balance_config()
        config.reload()
        
        self.caller.msg("配置文件已重新加载")

# 快速开始指南

> 本文档帮助新开发者快速上手金庸武侠MUD项目。

---

## 环境准备

### 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.11 或更高版本
- **内存**: 4GB+ 推荐
- **磁盘空间**: 1GB+

### 安装Python

```bash
# 检查Python版本
python --version

# 如果版本低于3.11，请安装新版
# 推荐从 https://www.python.org/downloads/ 下载
```

---

## 项目设置

### 1. 克隆仓库

```bash
git clone https://github.com/tomatoj23/MyMud.git
cd MyMud
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装生产依赖
pip install -e .

# 安装开发依赖（包含测试工具）
pip install -e ".[dev]"
```

### 4. 验证安装

```bash
# 运行测试
pytest tests/unit/ -q

# 预期输出：
# ============================= test session starts =============================
# ...
# ========================= 1023 passed in X.XXs ==============================
```

---

## 第一个游戏对象

### 创建房间

```python
import asyncio
from src.engine.core.engine import create_engine
from src.utils.config import Config

async def main():
    # 创建引擎
    config = Config()
    engine = create_engine(config)
    
    # 初始化引擎
    await engine.initialize()
    
    # 创建一个房间
    room = await engine.objects.create(
        typeclass_path="src.game.typeclasses.room.Room",
        key="test_room",
        attributes={
            "desc": "这是一个测试房间，四周空荡荡的。"
        }
    )
    
    print(f"创建房间成功，ID: {room.id}, Key: {room.key}")
    print(f"房间描述: {room.db.get('desc')}")
    
    # 清理
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

保存为 `create_room.py` 并运行：

```bash
python create_room.py
```

---

### 创建角色

```python
import asyncio
from src.engine.core.engine import create_engine

async def main():
    engine = create_engine()
    await engine.initialize()
    
    # 创建玩家角色
    player = await engine.objects.create(
        typeclass_path="src.game.typeclasses.character.Character",
        key="player1",
        attributes={
            "level": 1,
            "birth_talents": {
                "gengu": 20,
                "wuxing": 18,
                "fuyuan": 15,
                "rongmao": 16
            }
        }
    )
    
    print(f"创建角色: {player.key}")
    print(f"等级: {player.level}")
    print(f"根骨: {player.gengu}")
    
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 添加自定义命令

### 1. 创建命令文件

`src/game/commands/my_commands.py`:

```python
"""自定义命令示例。"""

from src.engine.commands.command import Command

class CmdHello(Command):
    """
    打招呼命令
    
    用法: hello [对象名]
    """
    key = "hello"
    aliases = ["hi", "你好"]
    
    async def func(self):
        """执行命令。"""
        target = self.args.strip()
        
        if target:
            self.msg(f"你向 {target} 热情地打招呼！")
        else:
            self.msg("你向大家打招呼：大家好！")
```

### 2. 注册命令

在 `src/game/commands/__init__.py` 中添加：

```python
from .my_commands import CmdHello

# 默认命令集
default_cmdset = CmdSet()
default_cmdset.add(CmdHello)
```

### 3. 测试命令

```python
import asyncio
from src.engine.core.engine import create_engine

async def main():
    engine = create_engine()
    await engine.initialize()
    await engine.start()
    
    # 创建测试角色
    player = await engine.objects.create(
        typeclass_path="src.game.typeclasses.character.Character",
        key="test_player"
    )
    
    # 处理命令
    result = await engine.process_input("session1", "hello")
    print(result)
    
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 创建自定义类型类

### 示例：创建一种特殊的武器

`src/game/typeclasses/weapons.py`:

```python
"""自定义武器类型。"""

from src.game.typeclasses.equipment import Equipment, EquipmentSlot

class Sword(Equipment):
    """剑类武器。"""
    
    typeclass_path = "src.game.typeclasses.weapons.Sword"
    
    @property
    def damage(self) -> int:
        """基础伤害。"""
        base = self.stats_bonus.get("damage", 10)
        quality_multiplier = self.quality.value * 0.2
        return int(base * quality_multiplier)
    
    def get_desc(self) -> str:
        """获取描述。"""
        return (
            f"这是一把{self.quality.name}品质的{self.name}，"
            f"伤害: {self.damage}"
        )
```

---

## 常用开发命令

### 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_combat.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 代码质量

```bash
# 格式化代码
black src/ tests/

# 静态检查
ruff check src/ tests/

# 类型检查
mypy src/

# 运行所有检查
make check
```

### 项目维护

```bash
# 清理临时文件
make clean

# 重新安装依赖
pip install -e ".[dev]" --force-reinstall
```

---

## 调试技巧

### 启用调试日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 使用断点

```python
import pdb; pdb.set_trace()
```

### 查看对象属性

```python
# 打印对象所有属性
print(dir(obj))

# 打印对象db属性
print(obj.db.all())
```

---

## 下一步

- [开发规范](./coding_standards.md) - 代码风格、提交规范
- [架构说明](../architecture/overview.md) - 系统架构设计
- [API文档](../api/core_api.md) - 核心API参考

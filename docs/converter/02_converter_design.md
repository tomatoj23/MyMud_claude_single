# xkx100 内容转换器技术设计方案

> 将 xkx100 (LPC) 内容转换为 JYMUD (Python/JSON) 格式的完整技术方案
> 版本: 1.0
> 日期: 2026-02-26

---

## 目录

1. [设计目标与约束](#一设计目标与约束)
2. [系统架构](#二系统架构)
3. [核心组件设计](#三核心组件设计)
4. [转换流程](#四转换流程)
5. [数据映射规范](#五数据映射规范)
6. [错误处理与验证](#六错误处理与验证)
7. [性能优化](#七性能优化)
8. [实施计划](#八实施计划)

---

## 一、设计目标与约束

### 1.1 设计目标

| 目标 | 优先级 | 说明 |
|:---|:---:|:---|
| **自动化** | P0 | 80%以上内容无需人工干预 |
| **可扩展** | P0 | 支持未来添加新的转换类型 |
| **可验证** | P0 | 转换结果可自动验证正确性 |
| **可追溯** | P1 | 保留原始数据来源信息 |
| **可恢复** | P1 | 支持增量转换和错误恢复 |
| **高性能** | P2 | 5000+文件在5分钟内完成 |

### 1.2 技术约束

| 约束 | 说明 |
|:---|:---|
| **不修改源码** | 转换器只读xkx100文件 |
| **兼容Python 3.11+** | 使用现代Python特性 |
| **类型安全** | 全程使用类型注解 |
| **异步支持** | 支持异步IO提高性能 |
| **纯文本中间格式** | JSON/YAML便于人工审核 |

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      xkx100-to-JYMUD 转换器                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   输入层     │───→│   解析层     │───→│   转换层     │       │
│  │  (Input)     │    │  (Parser)    │    │ (Transformer)│       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ↓                   ↓                   ↓                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ FileReader   │    │ Lexer        │    │ RoomMapper   │       │
│  │ PathResolver │    │ Tokenizer    │    │ NPCMapper    │       │
│  │ EncodingDet  │    │ ASTBuilder   │    │ SkillMapper  │       │
│  └──────────────┘    └──────────────┘    │ ItemMapper   │       │
│                                          └──────────────┘       │
│                                                   │              │
│                                                   ↓              │
│                                          ┌──────────────┐       │
│                                          │   输出层     │       │
│                                          │  (Output)    │       │
│                                          └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖

```
CLI Entry → ConverterPipeline → [LPCParser → Mappers → OutputWriter]
                ↓
        [ConfigManager, Logger, Validator, CacheManager]
```

---

## 三、核心组件设计

### 3.1 配置管理 (ConfigManager)

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ConverterConfig:
    """转换器配置"""
    
    xkx100_path: Path                    # xkx100项目路径
    output_path: Path                    # 输出目录
    schema_path: Path                    # JSON Schema路径
    
    enabled_converters: List[str] = field(
        default_factory=lambda: ["room", "npc", "item", "skill", "quest"]
    )
    
    max_workers: int = 8                 # 并行工作线程
    batch_size: int = 100                # 批处理大小
    
    output_format: str = "json"          # json/yaml/both
    pretty_print: bool = True            # 格式化输出
    validate_output: bool = True         # 验证输出
```

### 3.2 LPC解析器 (简化设计)

```python
from typing import Dict, List, Any, Optional
import re


class LPCParser:
    """LPC文件解析器"""
    
    def __init__(self, source: str, filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
    
    def parse(self) -> Dict[str, Any]:
        """解析LPC文件，提取关键数据"""
        result = {
            "filename": self.filename,
            "inherits": self._extract_inherits(),
            "properties": self._extract_properties(),
            "functions": self._extract_functions(),
        }
        return result
    
    def _extract_inherits(self) -> List[str]:
        """提取继承声明"""
        pattern = r'inherit\s+(\w+);'
        return re.findall(pattern, self.source)
    
    def _extract_properties(self) -> Dict[str, Any]:
        """提取set()调用中的属性"""
        properties = {}
        
        # 匹配 set("key", value) 或 set("key", ([...]))
        pattern = r'set\(\s*"([^"]+)"\s*,\s*(.+?)\s*\)\s*;'
        matches = re.findall(pattern, self.source, re.DOTALL)
        
        for key, value_str in matches:
            properties[key] = self._parse_value(value_str)
        
        return properties
    
    def _parse_value(self, value_str: str) -> Any:
        """解析LPC值"""
        value_str = value_str.strip()
        
        # 字符串
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        
        # 整数
        if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
            return int(value_str)
        
        # mapping: (["key": value, ...])
        if value_str.startswith('([') and value_str.endswith('])'):
            return self._parse_mapping(value_str[2:-2])
        
        # array: ({value, ...})
        if value_str.startswith('({') and value_str.endswith('})'):
            return self._parse_array(value_str[2:-2])
        
        # heredoc: @LONG ... LONG
        heredoc_match = re.match(r'@(\w+)\s*(.+?)\s*\1', value_str, re.DOTALL)
        if heredoc_match:
            return heredoc_match.group(2).strip()
        
        return value_str
    
    def _parse_mapping(self, content: str) -> Dict[str, Any]:
        """解析mapping内容"""
        result = {}
        # 简化解析：按逗号分割键值对
        pairs = self._split_mapping(content)
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip().strip('"')
                result[key] = self._parse_value(value.strip())
        return result
    
    def _parse_array(self, content: str) -> List[Any]:
        """解析array内容"""
        result = []
        # 简化解析：按逗号分割
        items = self._split_array(content)
        for item in items:
            result.append(self._parse_value(item.strip()))
        return result
    
    def _extract_functions(self) -> List[str]:
        """提取函数名列表"""
        pattern = r'(\w+)\s+([\w\s,]+)\([^)]*\)\s*\{'
        matches = re.findall(pattern, self.source)
        return [name for _, name in matches]
```

### 3.3 房间转换器 (RoomMapper)

```python
from typing import Dict, Any, List
from pathlib import Path


class RoomMapper:
    """房间数据转换器"""
    
    INHERIT_MAP = {
        'ROOM': 'room',
        'BUILD_ROOM': 'building',
        'MOUNTAIN_ROOM': 'mountain',
    }
    
    DIRECTION_MAP = {
        'north': '北', 'south': '南', 'east': '东', 'west': '西',
        'northeast': '东北', 'northwest': '西北',
        'southeast': '东南', 'southwest': '西南',
        'up': '上', 'down': '下', 'enter': '进入', 'out': '出去',
    }
    
    def can_map(self, parsed_data: Dict[str, Any]) -> bool:
        """检查是否可以转换"""
        inherits = parsed_data.get("inherits", [])
        return any(i in self.INHERIT_MAP for i in inherits)
    
    def map(self, parsed_data: Dict[str, Any], source_path: Path) -> Dict[str, Any]:
        """转换为JYMUD格式"""
        props = parsed_data.get("properties", {})
        
        result = {
            "type": "room",
            "source_file": str(source_path),
            "name": props.get("short", "未命名房间"),
            "description": self._clean_description(props.get("long", "")),
            "room_type": self._detect_room_type(parsed_data),
            "exits": self._convert_exits(props.get("exits", {}), source_path),
        }
        
        # 坐标
        if "coor/x" in props:
            result["position"] = {
                "x": props.get("coor/x", 0),
                "y": props.get("coor/y", 0),
                "z": props.get("coor/z", 0),
            }
        
        # 初始对象
        if "objects" in props:
            result["spawners"] = self._convert_spawners(props["objects"])
        
        # 标志
        flags = []
        if props.get("no_clean_up"):
            flags.append("persistent")
        if props.get("outdoors"):
            flags.append("outdoor")
        if props.get("no_fight"):
            flags.append("no_combat")
        if flags:
            result["flags"] = flags
        
        return result
    
    def _clean_description(self, text: str) -> str:
        """清理描述文本"""
        if not text:
            return ""
        # 去除颜色代码
        import re
        text = re.sub(r'\$[A-Z]+', '', text)
        return text.strip()
    
    def _detect_room_type(self, parsed_data: Dict) -> str:
        """检测房间类型"""
        for inherit in parsed_data.get("inherits", []):
            if inherit in self.INHERIT_MAP:
                return self.INHERIT_MAP[inherit]
        return "room"
    
    def _convert_exits(self, exits: Dict, source_path: Path) -> List[Dict]:
        """转换出口"""
        result = []
        current_dir = source_path.parent
        
        for direction, target in exits.items():
            exit_data = {
                "direction": direction,
                "direction_name": self.DIRECTION_MAP.get(direction, direction),
            }
            
            # 解析目标路径
            if isinstance(target, str):
                if target.startswith("__DIR__"):
                    target_path = target.replace("__DIR__", "")
                    exit_data["target"] = str(current_dir / target_path)
                elif target.startswith("/"):
                    exit_data["target"] = target
                else:
                    exit_data["target"] = target
                    exit_data["_unresolved"] = True
            
            result.append(exit_data)
        
        return result
    
    def _convert_spawners(self, objects: Dict) -> List[Dict]:
        """转换对象生成器"""
        return [
            {
                "object_path": path,
                "count": count,
                "respawn": True,
                "respawn_time": 300,
            }
            for path, count in objects.items()
        ]
```

### 3.4 NPC转换器 (NPCMapper)

```python
from typing import Dict, Any, Optional


class NPCMapper:
    """NPC数据转换器"""
    
    INHERIT_MAP = {
        'NPC': 'npc',
        'BOSS': 'boss',
        'VENDOR': 'vendor',
        'MASTER': 'master',
    }
    
    ATTRIBUTE_MAP = {
        'str': 'strength',
        'dex': 'dexterity',
        'con': 'constitution',
        'int': 'intelligence',
        'kar': 'fortune',
        'per': 'appearance',
    }
    
    def can_map(self, parsed_data: Dict[str, Any]) -> bool:
        inherits = parsed_data.get("inherits", [])
        return any(i in self.INHERIT_MAP for i in inherits)
    
    def map(self, parsed_data: Dict[str, Any], source_path: Path) -> Dict[str, Any]:
        props = parsed_data.get("properties", {})
        
        result = {
            "type": "npc",
            "npc_type": self._detect_npc_type(parsed_data),
            "source_file": str(source_path),
            "name": props.get("name", "未命名"),
            "gender": self._convert_gender(props.get("gender")),
            "age": props.get("age", 30),
            "description": self._clean_description(props.get("long", "")),
        }
        
        # 战斗属性
        combat = {
            "experience": props.get("combat_exp", 0),
            "max_hp": props.get("max_qi", 100),
            "max_sp": props.get("max_jing", 50),
            "max_mp": props.get("max_neili", 0),
        }
        
        # 先天属性
        attributes = {
            self.ATTRIBUTE_MAP.get(k, k): v
            for k, v in props.items()
            if k in self.ATTRIBUTE_MAP
        }
        if attributes:
            combat["attributes"] = attributes
        
        result["combat"] = combat
        
        return result
    
    def _convert_gender(self, gender: Optional[str]) -> str:
        mapping = {"男性": "male", "女性": "female", "无性": "none"}
        return mapping.get(gender, "unknown")
```

---

## 四、转换流程

### 4.1 主流程 (ConverterPipeline)

```python
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor


class ConverterPipeline:
    """转换流程编排器"""
    
    def __init__(self, config: ConverterConfig):
        self.config = config
        self.mappers = self._init_mappers()
        self.logger = self._init_logger()
    
    def _init_mappers(self) -> List[Any]:
        """初始化所有转换器"""
        from .mappers import RoomMapper, NPCMapper, ItemMapper, SkillMapper
        return [
            RoomMapper(),
            NPCMapper(),
            ItemMapper(),
            SkillMapper(),
        ]
    
    async def run(self) -> Dict[str, Any]:
        """执行完整转换流程"""
        self.logger.info("Starting conversion pipeline")
        
        # 1. 发现文件
        files = self._discover_files()
        self.logger.info(f"Found {len(files)} files to process")
        
        # 2. 分类文件
        categorized = self._categorize_files(files)
        
        # 3. 并行转换
        results = await self._convert_all(categorized)
        
        # 4. 验证输出
        if self.config.validate_output:
            self._validate_results(results)
        
        # 5. 写入输出
        self._write_output(results)
        
        # 6. 生成报告
        report = self._generate_report(results)
        
        return report
    
    def _discover_files(self) -> List[Path]:
        """发现所有LPC文件"""
        base_path = self.config.xkx100_path
        files = []
        
        # 搜索目录
        search_dirs = [
            base_path / "d",           # 地图
            base_path / "kungfu" / "skill",  # 武功
            base_path / "clone",       # 克隆对象
            base_path / "quest",       # 任务
        ]
        
        for directory in search_dirs:
            if directory.exists():
                files.extend(directory.rglob("*.c"))
        
        return files
    
    def _categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """按类型分类文件"""
        categories = {
            "room": [],
            "npc": [],
            "item": [],
            "skill": [],
            "quest": [],
            "unknown": [],
        }
        
        for file_path in files:
            # 简单启发式分类
            if "/npc/" in str(file_path):
                categories["npc"].append(file_path)
            elif "/obj/" in str(file_path) or "/clone/" in str(file_path):
                categories["item"].append(file_path)
            elif "/kungfu/" in str(file_path):
                categories["skill"].append(file_path)
            elif "/quest/" in str(file_path):
                categories["quest"].append(file_path)
            elif str(file_path).endswith(".c"):
                categories["room"].append(file_path)
            else:
                categories["unknown"].append(file_path)
        
        return categories
    
    async def _convert_all(self, categorized: Dict[str, List[Path]]) -> Dict[str, List[Any]]:
        """并行转换所有文件"""
        results = {}
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            for category, files in categorized.items():
                if category not in self.config.enabled_converters:
                    continue
                
                self.logger.info(f"Converting {len(files)} {category} files")
                
                # 批量处理
                futures = [
                    loop.run_in_executor(executor, self._convert_file, file_path)
                    for file_path in files
                ]
                
                category_results = await asyncio.gather(*futures, return_exceptions=True)
                
                # 过滤错误
                results[category] = [
                    r for r in category_results
                    if not isinstance(r, Exception)
                ]
                
                errors = [r for r in category_results if isinstance(r, Exception)]
                if errors:
                    self.logger.warning(f"{len(errors)} errors in {category}")
        
        return results
    
    def _convert_file(self, file_path: Path) -> Any:
        """转换单个文件"""
        try:
            # 1. 读取文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # 2. 解析LPC
            parser = LPCParser(source, str(file_path))
            parsed = parser.parse()
            
            # 3. 查找合适的转换器
            for mapper in self.mappers:
                if mapper.can_map(parsed):
                    return mapper.map(parsed, file_path)
            
            # 无匹配转换器
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to convert {file_path}: {e}")
            raise
    
    def _write_output(self, results: Dict[str, List[Any]]) -> None:
        """写入输出文件"""
        import json
        
        output_path = self.config.output_path
        output_path.mkdir(parents=True, exist_ok=True)
        
        for category, items in results.items():
            if not items:
                continue
            
            # 按区域组织
            by_area = self._organize_by_area(items)
            
            for area, area_items in by_area.items():
                area_dir = output_path / category / area
                area_dir.mkdir(parents=True, exist_ok=True)
                
                # 每个文件一个JSON
                for item in area_items:
                    filename = self._generate_filename(item)
                    filepath = area_dir / f"{filename}.json"
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(
                            item, f,
                            ensure_ascii=False,
                            indent=2 if self.config.pretty_print else None
                        )
    
    def _organize_by_area(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """按区域组织项目"""
        by_area = {}
        for item in items:
            source = item.get("source_file", "")
            # 从路径提取区域名
            parts = Path(source).parts
            if "d" in parts:
                idx = parts.index("d")
                area = parts[idx + 1] if idx + 1 < len(parts) else "misc"
            else:
                area = "misc"
            
            by_area.setdefault(area, []).append(item)
        
        return by_area
    
    def _generate_filename(self, item: Dict) -> str:
        """生成文件名"""
        name = item.get("name", "unnamed")
        # 转换为安全的文件名
        import re
        safe_name = re.sub(r'[^\w\-]', '_', name)
        return safe_name[:50]  # 限制长度
    
    def _generate_report(self, results: Dict[str, List[Any]]) -> Dict[str, Any]:
        """生成转换报告"""
        report = {
            "timestamp": self._get_timestamp(),
            "summary": {
                category: len(items)
                for category, items in results.items()
            },
            "total_converted": sum(len(items) for items in results.values()),
            "config": {
                "xkx100_path": str(self.config.xkx100_path),
                "output_path": str(self.config.output_path),
            }
        }
        
        # 保存报告
        import json
        report_path = self.config.output_path / "conversion_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
```

---

## 五、数据映射规范

### 5.1 房间映射表

| LPC属性 | JYMUD属性 | 转换规则 |
|:---|:---|:---|
| `inherit ROOM` | `type: "room"` | 直接映射 |
| `set("short", X)` | `name` | 字符串 |
| `set("long", X)` | `description` | 清理颜色代码 |
| `set("exits", {...})` | `exits: [...]` | 数组转换 |
| `set("objects", {...})` | `spawners: [...]` | 生成器配置 |
| `set("coor/*", X)` | `position: {x,y,z}` | 坐标对象 |
| `set("no_clean_up", 1)` | `flags: ["persistent"]` | 标志数组 |
| `set("outdoors", X)` | `flags: ["outdoor"]` | 户外标志 |
| `valid_leave()` | `conditions: [...]` | 需人工处理 |

### 5.2 NPC映射表

| LPC属性 | JYMUD属性 | 转换规则 |
|:---|:---|:---|
| `inherit NPC` | `type: "npc"` | 直接映射 |
| `set_name(zh, ids)` | `name`, `id` | 解析名称和ID列表 |
| `set("gender", X)` | `gender` | 映射为英文 |
| `set("age", X)` | `age` | 整数 |
| `set("long", X)` | `description` | 清理文本 |
| `set("str/dex/con/int", X)` | `combat.attributes` | 属性映射 |
| `set("max_qi", X)` | `combat.max_hp` | 气血映射 |
| `set("max_jing", X)` | `combat.max_sp` | 精神映射 |
| `set("max_neili", X)` | `combat.max_mp` | 内力映射 |
| `set("combat_exp", X)` | `combat.experience` | 经验映射 |
| `set_skill(X, Y)` | `skills.levels` | 技能等级 |
| `map_skill(X, Y)` | `skills.mappings` | 技能映射 |
| `set("chat_msg", [...])` | `dialogue.idle` | 对话系统 |
| `init()` | `behaviors` | 需人工处理 |

### 5.3 武功映射表

| LPC属性 | JYMUD属性 | 转换规则 |
|:---|:---|:---|
| `inherit SKILL` | `type: "skill"` | 招式 |
| `inherit FORCE` | `type: "force"` | 内功 |
| `type()` | `category` | martial/knowledge |
| `martialtype()` | `subcategory` | force/skill |
| `action`数组 | `moves: [...]` | 招式列表 |
| `valid_learn()` | `requirements` | 条件提取 |
| `valid_enable()` | `compatible_slots` | 可用位置 |
| `learn_bonus()` | `learn_rate` | 学习加成 |
| `query_action()` | `action_generator` | 需重写 |

### 5.4 物品映射表

| LPC属性 | JYMUD属性 | 转换规则 |
|:---|:---|:---|
| `inherit WEAPON` | `type: "weapon"` | 武器 |
| `inherit ARMOR` | `type: "armor"` | 防具 |
| `inherit ITEM` | `type: "item"` | 物品 |
| `set_name(X, Y)` | `name`, `id` | 名称和ID |
| `set("weight", X)` | `weight` | 重量(克) |
| `set("value", X)` | `value` | 价值 |
| `init_sword(X)` | `damage` | 武器伤害 |
| `set("armor_prop/armor", X)` | `defense` | 防御值 |
| `set("material", X)` | `material` | 材料 |
| `set("wield_msg", X)` | `equip_message` | 装备消息 |

---

## 六、错误处理与验证

### 6.1 错误分类

| 级别 | 类型 | 处理方式 |
|:---|:---|:---|
| **ERROR** | 语法解析失败 | 记录并跳过 |
| **ERROR** | 必需的属性缺失 | 记录并跳过 |
| **WARNING** | 未知属性 | 记录并保留 |
| **WARNING** | 路径解析失败 | 标记为未解析 |
| **INFO** | 使用默认值 | 记录 |

### 6.2 验证规则

```python
from jsonschema import validate, ValidationError


class OutputValidator:
    """输出验证器"""
    
    def __init__(self, schema_path: Path):
        self.schemas = self._load_schemas(schema_path)
    
    def validate_room(self, data: Dict) -> List[str]:
        """验证房间数据"""
        errors = []
        
        # 必需字段
        required = ["type", "name", "description"]
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # 类型检查
        if data.get("type") != "room":
            errors.append(f"Invalid type: {data.get('type')}")
        
        # 出口验证
        for exit_data in data.get("exits", []):
            if "direction" not in exit_data:
                errors.append("Exit missing direction")
            if "target" not in exit_data:
                errors.append("Exit missing target")
        
        return errors
    
    def validate_npc(self, data: Dict) -> List[str]:
        """验证NPC数据"""
        errors = []
        
        if "combat" in data:
            combat = data["combat"]
            if "max_hp" in combat and combat["max_hp"] < 1:
                errors.append("Invalid max_hp value")
        
        return errors
```

### 6.3 差异报告

```python
class DiffReporter:
    """差异报告生成器"""
    
    def generate_report(self, original: Dict, converted: Dict) -> Dict:
        """生成原始与转换后的差异报告"""
        report = {
            "source": original.get("source_file"),
            "missing_properties": [],
            "modified_properties": [],
            "added_properties": [],
        }
        
        # 获取原始属性
        original_props = self._extract_raw_properties(original)
        converted_props = converted
        
        # 检查缺失
        for key in original_props:
            if key not in converted_props and not key.startswith("_"):
                report["missing_properties"].append(key)
        
        # 检查新增
        for key in converted_props:
            if key not in original_props and not key.startswith("_"):
                report["added_properties"].append(key)
        
        return report
```

---

## 七、性能优化

### 7.1 并行处理策略

```
文件发现 → 分类 → [并行转换批次]
                ↓
        ┌───────┼───────┐
        ↓       ↓       ↓
     线程1   线程2   线程3
     房间    NPC     武功
        ↓       ↓       ↓
        └───────┼───────┘
                ↓
          结果合并 → 写入磁盘
```

### 7.2 缓存策略

```python
from functools import lru_cache
import hashlib


class ParseCache:
    """解析结果缓存"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, content: str) -> Optional[Dict]:
        """获取缓存"""
        key = self._get_cache_key(content)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            import json
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, content: str, result: Dict) -> None:
        """设置缓存"""
        key = self._get_cache_key(content)
        cache_file = self.cache_dir / f"{key}.json"
        
        import json
        with open(cache_file, 'w') as f:
            json.dump(result, f)
```

### 7.3 性能目标

| 指标 | 目标值 | 优化策略 |
|:---|:---:|:---|
| 单文件解析 | < 10ms | 正则优化、缓存 |
| 1000文件批量 | < 30s | 并行处理(8线程) |
| 5000文件完整转换 | < 5min | 流式处理、增量更新 |
| 内存占用 | < 2GB | 生成器、批量写入 |

---

## 八、实施计划

### 8.1 开发阶段

| 阶段 | 任务 | 工期 | 产出 |
|:---|:---|:---:|:---|
| **Phase 1** | LPC解析器开发 | 2天 | lpc_parser.py |
| **Phase 2** | 房间转换器 | 1天 | room_mapper.py + 测试 |
| **Phase 3** | NPC转换器 | 2天 | npc_mapper.py + 测试 |
| **Phase 4** | 武功转换器 | 1天 | skill_mapper.py + 测试 |
| **Phase 5** | 物品转换器 | 1天 | item_mapper.py + 测试 |
| **Phase 6** | 流程编排 | 2天 | pipeline.py + CLI |
| **Phase 7** | 验证与报告 | 2天 | validator.py + reporter |
| **总计** | | **11天** | |

### 8.2 目录结构

```
tools/
└── xkx_converter/
    ├── __init__.py
    ├── cli.py                    # 命令行入口
    ├── config.py                 # 配置管理
    ├── pipeline.py               # 主流程
    ├── lpc_parser.py             # LPC解析器
    ├── cache.py                  # 缓存管理
    ├── validator.py              # 验证器
    ├── reporter.py               # 报告生成
    └── mappers/
        ├── __init__.py
        ├── base_mapper.py        # 基类
        ├── room_mapper.py        # 房间
        ├── npc_mapper.py         # NPC
        ├── skill_mapper.py       # 武功
        ├── item_mapper.py        # 物品
        └── quest_mapper.py       # 任务
```

### 8.3 使用示例

```bash
# 完整转换
python -m tools.xkx_converter convert \
    --source D:/My_Projects/xkx100-20201118/xkx100-20201118 \
    --output ./converted_content \
    --workers 8

# 只转换特定类型
python -m tools.xkx_converter convert --types room,npc

# 只转换特定区域
python -m tools.xkx_converter convert --areas city,shaolin,wudang

# 验证转换结果
python -m tools.xkx_converter validate --input ./converted_content

# 生成差异报告
python -m tools.xkx_converter diff --original <lpc_file> --converted <json_file>
```

---

*文档版本: 1.0*
*最后更新: 2026-02-26*

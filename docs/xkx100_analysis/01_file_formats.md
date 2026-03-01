# xkx100 内容文件格式详细分析

> 本文档详细分析 xkx100 (侠客行100) 项目中各类内容文件的格式结构
> 分析日期: 2026-02-26
> 目标: 为数据转换提供技术依据

---

## 目录

1. [LPC语言基础](#一lpc语言基础)
2. [文件类型总览](#二文件类型总览)
3. [房间文件格式](#三房间文件格式)
4. [NPC文件格式](#四npc文件格式)
5. [武功技能文件格式](#五武功技能文件格式)
6. [物品文件格式](#六物品文件格式)
7. [任务文件格式](#七任务文件格式)
8. [数据提取要点](#八数据提取要点)

---

## 一、LPC语言基础

### 1.1 LPC语法概览

LPC（Lars Pensjö C）是MUD游戏专用脚本语言，具有以下特点：

| 特性 | 语法 | 说明 |
|:---|:---|:---|
| **继承** | `inherit CLASS;` | 多重继承 |
| **数据类型** | `int`, `string`, `object`, `mapping`, `array` | 动态类型 |
| **映射** | `(["key": value])` | 关联数组 |
| **数组** | `({a, b, c})` | 有序列表 |
| **函数指针** | `(: func, arg :)` | 闭包支持 |
| **宏定义** | `#define NAME value` | 预处理器 |
| **字符串块** | `@TEXT ... TEXT` | 多行字符串 |

### 1.2 核心宏定义

```lpc
// 目录宏（在配置中定义）
__DIR__          // 当前文件所在目录
__FILE__         // 当前文件完整路径

// 常见颜色宏（在ansi.h中）
NOR              // 恢复正常
BLK, RED, GRN, YEL, BLU, MAG, CYN, WHT     // 暗色
HBK, HIR, HIG, HIY, HIB, HIM, HIC, HIW    // 高亮

// 方向宏（在room.h中）
NORTH, SOUTH, EAST, WEST, NORTHEAST, ...   // 基本方向
ENTER, OUT                                  // 进出
```

### 1.3 标准函数

```lpc
// 对象操作
this_object()    // 获取当前对象
this_player()    // 获取当前玩家
present(id, env) // 在环境中查找对象
find_object(path) // 查找已加载对象

// 对象创建
new(path)        // 创建新对象
clonep(ob)       // 判断是否为克隆对象

// 定时器
call_out(func, delay, args...)  // 延迟调用
remove_call_out(func)           // 取消延迟调用

// 消息
write(msg)       // 写给玩家
say(msg)         // 说给房间内所有人
tell_object(ob, msg)  // 写给特定对象
message(type, msg, target, exclude)  // 广播消息

// 数据库操作
set(key, value)  // 设置持久属性
query(key)       // 查询属性
set_temp(key, value)  // 设置临时属性
query_temp(key)  // 查询临时属性
add(key, value)  // 增加值
delete(key)      // 删除属性

// 移动
move_object(ob)  // 移动对象
environment(ob)  // 获取环境
```

---

## 二、文件类型总览

### 2.1 文件分类表

| 类型 | 路径模式 | 文件数估算 | 关键特征 |
|:---|:---|:---:|:---|
| **房间** | `/d/<area>/*.c` | 5,000+ | `inherit ROOM;` |
| **NPC** | `/d/<area>/npc/*.c` | 2,000+ | `inherit NPC;` |
| **物品** | `/d/<area>/obj/*.c`, `/clone/*/*.c` | 1,000+ | `inherit ITEM/WEAPON/ARMOR;` |
| **武功** | `/kungfu/skill/*/*.c` | 300+ | `inherit SKILL/FORCE;` |
| **任务** | `/quest/*.c`, `/d/<area>/quest*.c` | 50+ | 特殊任务逻辑 |
| **基础类** | `/inherit/*/*.c` | 50+ | 被继承的基类 |
| **守护进程** | `/adm/daemons/*.c` | 40+ | 系统服务 |
| **命令** | `/cmds/*/*.c` | 200+ | 玩家指令 |

### 2.2 文件命名规范

```
房间文件:      <name>.c           如: beiliuxiang.c, guangchang.c
NPC文件:       <name>.c           如: bing.c, wang.c
物品文件:      <name>.c           如: gangdao.c, cloth.c
武功文件:      <pinyin>.c         如: damo-jian.c, bahuang-gong.c
基础类:        <name>.c           如: char.c, room.c, weapon.c
```

---

## 三、房间文件格式

### 3.1 标准房间结构

```lpc
// 文件头注释
// Room: /d/city/bingyindamen.c
// Author: YZC
// Date: 1995/12/04

// 包含头文件
#include <ansi.h>      // 颜色定义
#include <room.h>      // 房间宏

// 继承声明
inherit ROOM;

// 可选：门的数据（有门的房间）
nosave mapping doors;

// 创建函数（必须）
void create()
{
    // ===== 基础属性 =====
    set("short", "兵营大门");                    // 短名称
    set("long", @LONG                              // 详细描述
你正站在兵营的门口，面对着一排简陋的营房，可以看到穿着制服
的官兵正在操练，不时地传来呐喊声。老百姓是不允许在此观看的，你
最好赶快走开。
LONG );
    
    // ===== 出口定义 =====
    set("exits", ([                                 // 出口映射
        "south" : __DIR__"bingyin",               // 方向: 目标房间
        "north" : __DIR__"hejiajie",
        "east"  : __DIR__"dongjie",
    ]));
    
    // ===== 初始对象 =====
    set("objects", ([                               // 初始对象映射
        __DIR__"npc/bing" : 2,                    // 路径: 数量
        __DIR__"obj/gangdao" : 1,
    ]));
    
    // ===== 坐标（部分房间有）=====
    set("coor/x", 20);                             // X坐标
    set("coor/y", -60);                            // Y坐标
    set("coor/z", 0);                              // Z坐标
    
    // ===== 特殊属性 =====
//  set("no_clean_up", 0);                        // 不清理（已注释）
    set("outdoors", "city");                       // 户外区域
    
    // 完成初始化
    setup();
}

// 可选：自定义离开检查
int valid_leave(object me, string dir)
{
    // 检查逻辑
    if (!wizardp(me) && objectp(present("guan bing", environment(me))) && 
        dir == "south")
        return notify_fail("官兵拦住了你的去路。\n");
    
    // 调用父类方法
    return ::valid_leave(me, dir);
}
```

### 3.2 房间属性详解

| 属性名 | 类型 | 必需 | 说明 |
|:---|:---:|:---:|:---|
| `short` | string | ✅ | 房间短名称（显示用） |
| `long` | string | ✅ | 详细描述 |
| `exits` | mapping | ✅ | 出口映射 {方向: 路径} |
| `objects` | mapping | ❌ | 初始对象 {路径: 数量} |
| `coor/x` | int | ❌ | X坐标 |
| `coor/y` | int | ❌ | Y坐标 |
| `coor/z` | int | ❌ | Z坐标 |
| `no_clean_up` | int | ❌ | 1=不自动清理 |
| `outdoors` | string | ❌ | 户外区域标识 |
| `item_desc` | mapping | ❌ | 物品描述映射 |
| `resource` | mapping | ❌ | 资源点（挖矿等） |

### 3.3 出口方向枚举

```lpc
// 基本方向
"north", "south", "east", "west"
"northeast", "northwest", "southeast", "southwest"
"up", "down"
"enter", "out"

// 特殊方向（任意字符串）
"gate", "door", "ladder", ...
```

### 3.4 带门的房间

```lpc
inherit ROOM;

void create()
{
    set("short", "大门");
    set("long", "这里有一道大门...");
    set("exits", ([
        "north" : __DIR__"inner",
        "south" : __DIR__"outer",
    ]));
    setup();
}

// 创建门（在setup后调用）
void init()
{
    ::init();
    create_door("north", "大门", "south", DOOR_CLOSED);
    // 参数: 方向, 名称/配置, 对面方向, 初始状态
}
```

### 3.5 特殊房间变体

```lpc
// ===== 室内房间 =====
inherit ROOM;
void create() {
    set("short", "客栈房间");
    set("long", "这是一间客房...");
    // 无 outdoors 属性 = 室内
    set("sleep_room", 1);           // 可睡觉
    set("no_fight", 1);             // 禁止战斗
    set("no_magic", 1);             // 禁止魔法
}

// ===== 商店 =====
inherit ROOM;
void create() {
    set("short", "杂货铺");
    set("long", "这是一家杂货铺...");
    set("objects", ([
        __DIR__"npc/shopkeeper" : 1,
    ]));
}

// ===== 迷宫房间 =====
inherit ROOM;
void create() {
    set("short", "迷宫");
    set("long", "这里是迷宫...");
    set("maze", 1);                 // 标记为迷宫
    set("maze_zone", "taohua");     // 迷宫区域
}
```

---

## 四、NPC文件格式

### 4.1 标准NPC结构

```lpc
// NPC: /d/city/npc/bing.c
// 官兵

#include <ansi.h>
inherit NPC;

void create()
{
    // ===== 名称定义 =====
    set_name("官兵", ({ "guan bing", "bing" }));
    // 参数: 中文名, 英文ID列表
    
    // ===== 基础属性 =====
    set("age", 22);                               // 年龄
    set("gender", "男性");                         // 性别
    set("long", "虽然官兵的武艺不能和武林人士相比，可是他们讲究的是人多力量大。\n");
    set("attitude", "peaceful");                   // 态度
    
    // ===== 战斗属性 =====
    set("str", 24);                               // 膂力
    set("dex", 16);                               // 身法
    set("con", 20);                               // 根骨
    set("int", 15);                               // 悟性
    set("kar", 10);                               // 福缘
    set("per", 12);                               // 容貌
    
    // ===== 气血内力 =====
    set("max_qi", 200);                           // 最大气血
    set("max_jing", 100);                         // 最大精神
    set("max_neili", 100);                        // 最大内力
    set("jiali", 10);                             // 加力
    
    // ===== 经验 =====
    set("combat_exp", 10000);                     // 实战经验
    set("shen_type", 1);                          // 正神类型(1正/-1邪)
    
    // ===== 武功技能 =====
    set_skill("unarmed", 40);                     // 基本拳脚
    set_skill("dodge", 40);                       // 基本躲闪
    set_skill("parry", 40);                       // 基本招架
    set_skill("blade", 40);                       // 基本刀法
    set_skill("force", 40);                       // 基本内功
    
    // 技能映射（使用特定武功）
    map_skill("blade", "fanliangyi-dao");         // 刀法映射
    map_skill("parry", "fanliangyi-dao");         // 招架映射
    map_skill("dodge", "xiaoyaoyou");             // 轻功映射
    map_skill("force", "huntian-qigong");         // 内功映射
    
    // 预备技能（空手使用）
    prepare_skill("strike", "xianglong-zhang");   // 预备掌法
    
    // ===== 临时属性加成 =====
    set_temp("apply/attack", 40);                 // 攻击加成
    set_temp("apply/defense", 40);                // 防御加成
    set_temp("apply/damage", 20);                 // 伤害加成
    set_temp("apply/armor", 40);                  // 护甲加成
    
    // ===== 对话设置 =====
    set("chat_chance", 10);                       // 聊天概率(%)
    set("chat_msg", ({                           // 聊天消息列表
        "官兵说道：不准在这里捣乱！\n",
        "官兵打了个哈欠。\n",
        (: random_move :),                       // 函数指针
    }));
    
    // 战斗时对话
    set("chat_chance_combat", 10);
    set("chat_msg_combat", ({
        "官兵喝道：大胆刁民，竟敢造反不成？\n",
        "官兵喝道：跑得了和尚跑不了庙，你还是快快束手就擒！\n",
    }));
    
    // ===== 询问响应 =====
    set("inquiry", ([                            // 询问映射
        "name" : "我是这里的官兵。\n",
        "here" : "这里是扬州城。\n",
        "rumors" : (: do_inquiry_rumors :),      // 函数响应
    ]));
    
    // ===== 携带物品 =====
    carry_object(__DIR__"obj/gangdao")->wield(); // 装备武器
    carry_object(__DIR__"obj/junfu")->wear();    // 穿戴防具
    carry_object("/clone/money/silver", 10);     // 携带银两
    
    // 完成初始化
    setup();
}

// ===== 交互函数 =====
void init()
{
    ::init();                                     // 调用父类
    
    object ob;
    // 如果是杀人犯，主动攻击
    if (interactive(ob = this_player()) && 
        (int)ob->query_condition("killer")) {
        remove_call_out("kill_ob");
        call_out("kill_ob", 1, ob);
    }
}

// 接受战斗
int accept_fight(object me)
{
    command("say 大爷我正想找人杀呐，今天算你倒霉。\n");
    me->apply_condition("killer", 500);           // 标记杀人犯
    kill_ob(me);
    return 1;
}

// 接受拜师
int accept_apprentice(object ob)
{
    // 收徒逻辑
    return 1;
}
```

### 4.2 NPC属性详解

#### 4.2.1 基础属性

| 属性名 | 类型 | 说明 |
|:---|:---:|:---|
| `name` | string | 名称（通过set_name设置） |
| `id` | string* | ID列表（通过set_name设置） |
| `title` | string | 称号 |
| `age` | int | 年龄 |
| `gender` | string | 性别：男性/女性/无性 |
| `long` | string | 详细描述 |
| `attitude` | string | 态度：friendly/peaceful/aggressive/killer |

#### 4.2.2 先天属性

| 属性名 | 类型 | 说明 | 范围 |
|:---|:---:|:---|:---:|
| `str` | int | 膂力（影响攻击） | 10-30 |
| `dex` | int | 身法（影响命中/闪避） | 10-30 |
| `con` | int | 根骨（影响气血/防御） | 10-30 |
| `int` | int | 悟性（影响学习速度） | 10-30 |
| `kar` | int | 福缘（影响奇遇） | 10-30 |
| `per` | int | 容貌（影响社交） | 10-30 |

#### 4.2.3 战斗属性

| 属性名 | 类型 | 说明 |
|:---|:---:|:---|
| `max_qi` | int | 最大气血 |
| `eff_qi` | int | 有效气血（受伤后低于max） |
| `qi` | int | 当前气血 |
| `max_jing` | int | 最大精神 |
| `eff_jing` | int | 有效精神 |
| `jing` | int | 当前精神 |
| `max_neili` | int | 最大内力 |
| `neili` | int | 当前内力 |
| `jiali` | int | 加力（额外伤害） |
| `combat_exp` | int | 实战经验 |
| `shen` | int | 神数值（正邪） |
| `shen_type` | int | 1=正派, -1=邪派 |

#### 4.2.4 技能系统

```lpc
// 设置技能等级
set_skill("skill_name", level);

// 技能映射（使用高级武功）
map_skill("skill_type", "advanced_skill");
// skill_type: unarmed/sword/blade/staff/whip/force/parry/dodge

// 预备技能（空手时使用）
prepare_skill("skill_type", "skill_name");
```

### 4.3 NPC特殊类型

```lpc
// ===== 商店老板 =====
inherit NPC;
inherit F_VENDOR;

void create() {
    set_name("掌柜", ({ "zhang gui" }));
    // ...
    set("vendor_goods", ({     // 出售商品列表
        "/clone/shop/item1",
        "/clone/shop/item2",
    }));
}

// ===== 师父（可拜师）=====
inherit NPC;
inherit F_MASTER;

void create() {
    set_name("洪七公", ({ "hong qigong" }));
    // ...
    set_skill("xianglong-zhang", 200);  // 必须设置才能教
    set("can_teach", ([
        "xianglong-zhang" : 1,
        "dagou-bang" : 1,
    ]));
}

// ===== 任务NPC =====
inherit NPC;

void init() {
    ::init();
    add_action("do_quest", "quest");     // 添加quest命令
}

int do_quest(string arg) {
    // 任务逻辑
    return 1;
}
```

---

## 五、武功技能文件格式

### 5.1 武功类型分类

| 类型 | 继承 | 功能 | 示例 |
|:---|:---|:---|:---|
| **内功** | `inherit FORCE;` | 内力修炼、特殊效果 | 八荒六合唯我独尊功 |
| **招式** | `inherit SKILL;` | 攻击招式 | 达摩剑、降龙十八掌 |
| **轻功** | `inherit SKILL;` | 闪避、移动 | 凌波微步、神行百变 |
| **招架** | `inherit SKILL;` | 被动防御 | 无特定招架技能 |
| **知识** | `inherit SKILL;` | 辅助技能 | 炼丹、锻造、读书写字 |

### 5.2 内功文件格式

```lpc
// bahuang-gong.c 八荒六合唯我独尊功
#include <ansi.h>
#include "force.h";           // 继承force.h中的宏
inherit FORCE;

// ===== 武功类型标识 =====
string type() { return "martial"; }      // 武术类
string martialtype() { return "force"; } // 内功类

// ===== 启用检查 =====
int valid_enable(string usage) { 
    return usage == "force";              // 只能作为内功使用
}

// ===== 学习条件 =====
int valid_learn(object me)
{
    // 门派限制
    if ((string)me->query("family/master_id") != "tong lao"
        && (string)me->query("family/master_id") != "xu zhu")
        return notify_fail("只有灵鹫宫门下弟子才能学习八荒六合唯我独尊功。\n");
    
    // 前置技能要求
    if ((int)me->query_skill("force", 1) < 10)
        return notify_fail("你的基本内功火候还不够。\n");
    
    // 互斥内功检查
    return valid_public(me, "beiming-shengong");
}

// ===== 练习限制 =====
int practice_skill(object me)
{
    return notify_fail("八荒六合唯我独尊功只能用学(learn)的来提高。\n");
}

// ===== 特殊功能文件 =====
string exert_function_file(string func)
{
    return __DIR__"bahuang-gong/" + func;
    // 指向: bahuang-gong/recover.c, bahuang-gong/transfer.c 等
}

// ===== 效果加成 =====
int learn_bonus() { return 0; }           // 学习加成
int practice_bonus() { return 0; }        // 练习加成
int success() { return 10; }               // 成功率加成
int power_point(object me) { return 1; }   // 威力系数

// ===== 帮助信息 =====
int help(object me)
{
    write(HIC"\n八荒六合唯我独尊功："NOR"\n");
    write(@HELP
    八荒六合唯我独尊功是灵鹫宫至高无上的内功，须以最上乘内
功为根基。这功夫威力奇大，却有一个大大的不利之处，每三十年，
便要返老还童一次。

    学习要求：
        灵鹫宫弟子
        基本内功10级
HELP
    );
    return 1;
}
```

### 5.3 招式武功文件格式

```lpc
// damo-jian.c 达摩剑
#include <ansi.h>
inherit SKILL;

string type() { return "martial"; }
string martialtype() { return "skill"; }  // 招式类

// ===== 招式定义 =====
mapping *action = ({
([  "action" : "$N使一式"MAG"「万事随缘往」"NOR"，手中$w嗡嗡微振，幻成一条疾光刺向$n的$l",
    "lvl" : 0,                               // 等级要求
    "skill_name" : "万事随缘往"              // 招式名
]),
([  "action" : "$N错步上前，使出"HIC"「来去若梦行」"NOR"，剑意若有若无，$w淡淡地向$n的$l挥去",
    "lvl" : 10,
    "skill_name" : "来去若梦行"
]),
([  "action" : "$N一式"YEL"「浮世沧桑远」"NOR"，纵身飘开数尺，运发剑气，手中$w遥摇指向$n的$l",
    "lvl" : 20,
    "skill_name" : "浮世沧桑远"
]),
// ... 更多招式
});

// ===== 启用检查 =====
int valid_enable(string usage) { 
    return usage == "sword" || usage == "parry";  // 可用于剑法和招架
}

// ===== 学习条件 =====
int valid_learn(object me)
{
    if ((int)me->query("max_neili") < 100)
        return notify_fail("你的内力不够。\n");
    if ((int)me->query_skill("hunyuan-yiqi", 1) < 20)
        return notify_fail("你的混元一气功火候太浅。\n");
    return 1;
}

// ===== 练习消耗 =====
int practice_skill(object me)
{
    object weapon;
    
    // 检查武器
    if (!objectp(weapon = me->query_temp("weapon"))
        || (string)weapon->query("skill_type") != "sword")
        return notify_fail("你使用的武器不对。\n");
    
    // 检查消耗
    if ((int)me->query("qi") < 30 || (int)me->query("neili") < 15)
        return notify_fail("你的内力或气不够练达摩剑。\n");
    
    // 扣除消耗
    me->receive_damage("qi", 30);
    me->add("neili", -15);
    return 1;
}

// ===== 获取招式名 =====
string query_skill_name(int level)
{
    int i;
    for (i = sizeof(action); i > 0; i--)
        if (level >= action[i-1]["lvl"])
            return action[i-1]["skill_name"];
}

// ===== 战斗时调用：获取招式数据 =====
mapping query_action(object me, object weapon)
{
    // 效果参数
    int d_e1 = 30;      // 闪避效果基础
    int d_e2 = 50;      // 闪避效果最大
    int p_e1 = 0;       // 招架效果基础
    int p_e2 = 20;      // 招架效果最大
    int f_e1 = 100;     // 内力效果基础
    int f_e2 = 150;     // 内力效果最大
    int m_e1 = 40;      // 伤害效果基础
    int m_e2 = 140;     // 伤害效果最大
    
    int i, lvl, seq, ttl = sizeof(action);
    
    // 根据等级选择可用招式
    lvl = (int) me->query_skill("damo-jian", 1);
    for (i = ttl; i > 0; i--)
        if (lvl > action[i-1]["lvl"]) {
            seq = i;
            break;
        }
    seq = random(seq);       // 随机选择
    
    // 返回招式数据
    return ([
        "action"      : action[seq]["action"],           // 招式描述
        "dodge"       : d_e1 + (d_e2 - d_e1) * seq / ttl, // 闪避加成
        "parry"       : p_e1 + (p_e2 - p_e1) * seq / ttl, // 招架加成
        "force"       : f_e1 + (f_e2 - f_e1) * seq / ttl, // 内力加成
        "damage"      : m_e1 + (m_e2 - m_e1) * seq / ttl, // 伤害加成
        "damage_type" : random(2) ? "割伤" : "刺伤",     // 伤害类型
    ]);
}

// ===== 效果加成 =====
int learn_bonus() { return 30; }
int practice_bonus() { return 30; }
int success() { return 20; }
int power_point() { return 1.0; }

// ===== 绝学文件 =====
string perform_action_file(string action)
{
    return __DIR__"damo-jian/" + action;
    // 指向: damo-jian/perform1.c 等
}
```

### 5.4 武功属性详解

| 属性/函数 | 类型 | 说明 |
|:---|:---:|:---|
| `type()` | string | 大类：martial/knowledge |
| `martialtype()` | string | 子类：force/skill |
| `valid_enable(usage)` | int | 检查能否用于某用途 |
| `valid_learn(me)` | int | 学习条件检查 |
| `practice_skill(me)` | int | 练习逻辑和消耗 |
| `query_action(me, weapon)` | mapping | 获取战斗招式 |
| `query_skill_name(lvl)` | string | 获取当前招式名 |
| `learn_bonus()` | int | 学习速度加成 |
| `practice_bonus()` | int | 练习效率加成 |
| `success()` | int | 使用成功率加成 |
| `power_point()` | float | 威力系数 |

### 5.5 招式数据mapping结构

```lpc
([
    "action"      : string,    // 招式描述文本（含颜色代码）
    "skill_name"  : string,    // 招式名称
    "lvl"         : int,       // 学习等级要求
    "dodge"       : int,       // 闪避加成值
    "parry"       : int,       // 招架加成值
    "force"       : int,       // 内力加成值
    "damage"      : int,       // 伤害加成值
    "damage_type" : string,    // 伤害类型：刺伤/割伤/瘀伤/内伤
])
```

---

## 六、物品文件格式

### 6.1 物品类型分类

| 类型 | 继承 | 用途 |
|:---|:---|:---|
| **普通物品** | `inherit ITEM;` | 可携带、查看的物品 |
| **武器** | `inherit WEAPON;` | 可装备用于战斗 |
| **防具** | `inherit ARMOR;` | 可装备用于防护 |
| **金钱** | `inherit MONEY;` | 货币 |
| **食物** | `inherit FOOD;` | 可食用恢复 |
| **药品** | `inherit MEDICINE;` | 恢复或治疗 |
| **书籍** | `inherit BOOK;` | 学习技能 |
| **容器** | `inherit CONTAINER;` | 可存放物品 |

### 6.2 武器文件格式

```lpc
// gangdao.c 钢刀

#include <weapon.h>
inherit BLADE;            // 继承刀类

void create()
{
    // ===== 名称定义 =====
    set_name("钢刀", ({ "blade", "dao", "gang dao" }));
    
    // ===== 基础属性 =====
    set_weight(7000);                           // 重量（克）
    
    // ===== 克隆对象处理 =====
    if (clonep())
        set_default_object(__FILE__);
    else {
        // ===== 非克隆属性（只设置一次）=====
        set("unit", "柄");                       // 量词
        set("long", "这是一柄亮晃晃的钢刀，普通官兵的常备武器。\n");
        set("value", 1000);                       // 价值（文）
        set("material", "steel");                 // 材料
        
        // 装备/卸下消息
        set("wield_msg", "$N「唰」的一声抽出一柄$n握在手中。\n");
        set("unwield_msg", "$N将手中的$n插回刀鞘。\n");
    }
    
    // ===== 武器初始化 =====
    init_blade(20);                              // 初始化刀，伤害20
    setup();
}
```

### 6.3 武器类型初始化函数

```lpc
// 在 /inherit/weapon/weapon.c 中定义

// 刀
varargs void init_blade(int damage, int flag) {
    set("weapon_prop/damage", damage);
    set("flag", flag | EDGED | SECONDARY);
    set("skill_type", "blade");
    set("rigidity", damage/3);           // 硬度
    set("verbs", ({ "slash", "slice", "hack" }));
}

// 剑
varargs void init_sword(int damage, int flag) {
    set("weapon_prop/damage", damage);
    set("flag", flag | EDGED | SECONDARY);
    set("skill_type", "sword");
    set("rigidity", damage/3);
    set("verbs", ({ "slash", "slice", "thrust" }));
}

// 其他类型类似...
```

### 6.4 防具文件格式

```lpc
// junfu.c 军服

#include <armor.h>
inherit CLOTH;            // 继承衣服类

void create()
{
    set_name("军服", ({ "jun fu", "cloth" }));
    set_weight(3000);
    
    if (clonep())
        set_default_object(__FILE__);
    else {
        set("unit", "件");
        set("long", "这是一件官兵常穿的军服。\n");
        set("value", 500);
        set("material", "cloth");
        
        // 穿戴部位
        set("armor_prop/armor", 10);              // 防御值
        set("armor_type", "cloth");               // 防具类型
        
        set("wear_msg", "$N穿上了一件$n。\n");
        set("remove_msg", "$N脱下了$n。\n");
    }
    
    setup();
}
```

### 6.5 物品属性详解

#### 通用属性

| 属性名 | 类型 | 说明 |
|:---|:---:|:---|
| `name` | string | 名称（通过set_name设置） |
| `id` | string* | ID列表 |
| `unit` | string | 量词：件、柄、把、个... |
| `long` | string | 详细描述 |
| `weight` | int | 重量（克） |
| `value` | int | 价值（文钱） |
| `material` | string | 材料：steel/iron/cloth/wood... |

#### 武器属性

| 属性名 | 类型 | 说明 |
|:---|:---:|:---|
| `skill_type` | string | 技能类型：sword/blade/spear/staff... |
| `weapon_prop/damage` | int | 伤害值 |
| `rigidity` | int | 硬度（耐久相关） |
| `flag` | int | 武器标志位 |
| `verbs` | string* | 动词列表 |
| `wield_msg` | string | 装备消息 |
| `unwield_msg` | string | 卸下消息 |

#### 防具属性

| 属性名 | 类型 | 说明 |
|:---|:---:|:---|
| `armor_type` | string | 类型：head/neck/armor/cloth/surcoat/waist/wrists/shield/finger/hands/boots |
| `armor_prop/armor` | int | 防御值 |
| `wear_msg` | string | 穿戴消息 |
| `remove_msg` | string | 卸下消息 |

---

## 七、任务文件格式

### 7.1 任务类型

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| **杀怪任务** | 击杀指定NPC | 赫连铁树任务 |
| **寻物任务** | 寻找指定物品 | 找回失物 |
| **护送任务** | 护送NPC到某地 | 护送商队 |
| **门派任务** | 门派日常 | 少林扫地 |
| **主线任务** | 剧情推进 | 华山论剑 |

### 7.2 任务NPC文件格式

```lpc
// helian.c 赫连铁树（任务发布者）

inherit NPC;
#include <ansi.h>

void create()
{
    // ===== 基础信息 =====
    set_name("赫连铁树", ({ "helian tieshu", "helian", "tieshu" }));
    set("title", HIY"西夏国征东大将军"HIM"西夏一品堂"HIR"总管"NOR);
    set("gender", "男性");
    set("age", 35);
    set("long", "他身穿大红锦袍，三十四五岁年纪，鹰钩鼻、八字须。\n");
    
    // ===== 战斗属性 =====
    set("combat_exp", 500000);
    set("shen_type", -1);
    set("attitude", "peaceful");
    set("max_qi", 2500);
    set("max_jing", 1000);
    set("neili", 2500);
    set("max_neili", 2500);
    
    // ===== 技能 =====
    set_skill("claw", 80);
    set_skill("force", 80);
    set_skill("parry", 80);
    set_skill("dodge", 40);
    set_skill("jiuyin-baiguzhao", 90);
    
    map_skill("claw", "jiuyin-baiguzhao");
    prepare_skill("claw", "jiuyin-baiguzhao");
    
    // ===== 询问响应 =====
    set("inquiry", ([
        "一品堂" : "一品堂就是要和中原武林做对！\n",
        "任务"   : (: give_quest :),
    ]));
    
    setup();
    carry_object(CLOTH_DIR"jinduan")->wear();
}

// ===== 初始化：添加命令 =====
void init()
{
    ::init();
    add_action("give_quest", "quest");      // 添加quest命令
    add_action("cancel_quest", "cancel");   // 添加cancel命令
}

// ===== 发布任务 =====
int give_quest()
{
    object me = this_player();
    mapping quest;
    int exp, level;
    
    // 检查是否已有任务
    if (me->query("quest")) {
        write("你已经有一个任务了。\n");
        return 1;
    }
    
    // 检查等级
    exp = me->query("combat_exp");
    if (exp < 10000) {
        write("你的经验太低，无法接取任务。\n");
        return 1;
    }
    
    // 生成任务
    quest = ([
        "name"      : "铲除恶霸",
        "target"    : "/d/city/npc/ebazhu",
        "target_name": "恶霸",
        "type"      : "kill",
        "reward_exp": exp / 10,
        "reward_pot": exp / 20,
        "time_limit": 600,                    // 10分钟
    ]);
    
    me->set("quest", quest);
    write("赫连铁树说道：你去铲除城里的恶霸，回来复命。\n");
    return 1;
}

// ===== 完成任务 =====
int accept_object(object me, object ob)
{
    mapping quest;
    
    if (!(quest = me->query("quest")))
        return 0;
    
    // 检查是否是任务物品
    if (ob->query("id") == quest["target_id"]) {
        write("赫连铁树说道：干得好！这是你的奖励。\n");
        
        // 发放奖励
        me->add("combat_exp", quest["reward_exp"]);
        me->add("potential", quest["reward_pot"]);
        me->delete("quest");
        
        return 1;
    }
    
    return 0;
}
```

### 7.3 任务数据结构

```lpc
// 标准任务mapping结构
mapping quest = ([
    "name"        : string,    // 任务名称
    "type"        : string,    // 类型: kill/find/escort
    "target"      : string,    // 目标路径（NPC或物品）
    "target_name" : string,    // 目标名称
    "target_id"   : string,    // 目标ID
    "location"    : string,    // 目标位置（寻物/护送）
    "reward_exp"  : int,       // 经验奖励
    "reward_pot"  : int,       // 潜能奖励
    "reward_money": int,       // 金钱奖励
    "time_limit"  : int,       // 时间限制（秒）
    "start_time"  : int,       // 开始时间
    "description" : string,    // 任务描述
]);
```

---

## 八、数据提取要点

### 8.1 LPC语法提取要点

| 模式 | 正则表达式 | 说明 |
|:---|:---|:---|
| 继承声明 | `inherit\s+(\w+);` | 提取继承的类 |
| 设置属性 | `set\("([^"]+)",\s*(.+?)\);` | 提取set调用 |
| 设置临时 | `set_temp\("([^"]+)",\s*(.+?)\);` | 提取set_temp |
| 名称定义 | `set_name\("([^"]+)",\s*\({([^}]+)}\)\)` | 提取名称和ID |
| 映射定义 | `\(\["([^"]+)":\s*(.+?)\]\)` | 提取mapping |
| 数组定义 | `\({([^}]+)}\)` | 提取array |
| 多行字符串 | `@(\w+)\s*(.+?)\s*\1` | 提取HEREDOC |
| 包含文件 | `#include\s*[<"]([^>"]+)[>"]` | 提取头文件 |
| 函数定义 | `(\w+)\s+([\w\s,]+)\([^)]*\)\s*\{` | 提取函数 |

### 8.2 特殊处理事项

| 事项 | 处理方式 |
|:---|:---|
| **颜色代码** | 提取并映射到你的项目的颜色系统 |
| **函数指针** | 标记为"需人工处理" |
| **条件编译** | `#ifdef`块内的内容需要条件判断 |
| **继承链** | 需要递归解析继承文件获取完整属性 |
| **__DIR__宏** | 替换为文件所在目录的相对路径 |
| **注释块** | `/* */`和`//`需要过滤 |
| **字符串转义** | 处理`\n`、 `"`等转义字符 |

### 8.3 需要人工审核的内容

| 类型 | 原因 | 示例 |
|:---|:---|:---|
| **自定义函数** | 逻辑无法自动转换 | `valid_leave()`, `accept_fight()` |
| **定时器调用** | 需要重新设计 | `call_out("func", time)` |
| **影子机制** | Python无直接对应 | `shadow(who, obj)` |
| **复杂条件** | 超出简单映射范围 | 多条件门派检查 |
| **特殊效果** | 需要重新实现 | 内功特殊效果 |
| **任务逻辑** | 流程复杂 | 多步骤任务链 |

---

## 九、附录

### 9.1 常用路径宏

```lpc
__DIR__              // 当前目录
__FILE__             // 当前文件
DATA_DIR             // /data/
LOG_DIR              // /log/
CMD_DIR              // /cmds/
FEATURE_DIR          // /feature/
INHERIT_DIR          // /inherit/
KUNGFU_DIR           // /kungfu/
QUEST_DIR            // /quest/
```

### 9.2 门派名称列表

```lpc
// 主要门派
"少林派"(shaolin)    "武当派"(wudang)     "峨眉派"(emei)
"华山派"(huashan)    "昆仑派"(kunlun)     "崆峒派"(kongtong)
"青城派"(qingcheng)  "全真教"(quanzhen)   "古墓派"(gumu)
"桃花岛"(taohua)     "丐帮"(gaibang)      "明教"(mingjiao)
"日月神教"(riyue)    "星宿派"(xingxiu)    "大理段氏"(dali)
"慕容世家"(murong)   "白驼山"(baituo)     "灵鹫宫"(lingjiu)
"神龙教"(shenlong)
```

### 9.3 武功类型枚举

```lpc
// 基本技能
force                // 内功
unarmed              // 拳脚
dodge                // 轻功
parry                // 招架
sword                // 剑法
blade                // 刀法
staff                // 棍法
spear                // 枪法
club                 // 杖法
hammer               // 锤法
whip                 // 鞭法
throwing             // 暗器
finger               // 指法
hand                 // 手法
claw                 // 爪法
cuff                 // 拳法
strike               // 掌法
leg                  // 腿法
```

---

*文档版本: 1.0*
*最后更新: 2026-02-26*
*数据来源: xkx100-20201118 侠客行100项目*

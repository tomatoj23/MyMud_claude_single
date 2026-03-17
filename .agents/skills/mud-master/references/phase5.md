> 当前进度注记（先看根目录文档）：
> - 当前状态：待开始（source of truth: `DEVELOPMENT_PLAN.md` / `TODO.md`）
> - 本文档属于未来阶段蓝图，文中的文件路径不要求当前仓库已经存在。
> - 开始实施前，先核对当前 `src/`、`tests/` 与根目录进度文档，再决定最终落地位置。

# 阶段五：内容制作与集成（第13-15周）

## 阶段目标

填充游戏内容：地图、任务、武学、NPC数据。本阶段结束时，应有一个可游玩的Demo版本。

## 模块清单

| 顺序 | 模块 | 依赖 | 状态 |
|:---|:---|:---|:---|
| 1 | 世界构建 - 金庸经典场景 | 阶段四完成 | 待开始 |
| 2 | 武学数据 - 十大门派基础武学 | 阶段四完成 | 待开始 |
| 3 | 任务与剧情 - 主线任务链 | 阶段四完成 | 待开始 |
| 4 | NPC数据 - 门派NPC | 阶段四完成 | 待开始 |

## 5.1 世界构建（第13周）

### 金庸经典场景

| 区域 | 房间数 | 特色 |
|:---|:---|:---|
| 襄阳城 | 30+ | 主城，客栈、武馆、集市 |
| 洛阳 | 25+ | 古都，皇城、书院 |
| 少林寺 | 40+ | 门派驻地，藏经阁、罗汉堂 |
| 武当山 | 35+ | 门派驻地，金顶、紫霄宫 |
| 华山 | 30+ | 门派驻地，思过崖、玉女峰 |
| 峨眉山 | 25+ | 门派驻地 |
| 桃花岛 | 20+ | 门派驻地，奇门遁甲 |
| 绝情谷 | 15+ | 秘境，情花毒 |
| 终南山 | 20+ | 古墓派，活死人墓 |

**任务清单：**
- [ ] 房间描述文案编写（每房间100-300字）
- [ ] 出口连接配置
- [ ] 环境属性设置（昼夜、天气影响）

**数据格式示例：**
```yaml
# resources/world/shaolin.yaml
area:
  key: shaolin
  name: 少林寺
  description: 天下武功出少林
  
rooms:
  - key: shaolin_shanmen
    name: 少林寺山门
    description: |
      你站在少林寺山门之前。两尊石狮威武雄壮，
      朱红山门上方悬挂"少林寺"金字匾额。
      山门两侧松柏森森，钟声悠扬。
    coords: [100, 100, 0]
    exits:
      south: luoyang_road_north
      north: shaolin_daxiong
    
  - key: shaolin_daxiong
    name: 大雄宝殿
    description: |
      少林寺主殿，供奉释迦牟尼佛。
      殿内香火鼎盛，僧众诵经声不绝于耳。
    coords: [100, 101, 0]
    exits:
      south: shaolin_shanmen
      north: shaolin_fangzhang
      east: shaolin_cangjing
      west: shaolin_luohan
```

## 5.2 武学数据（第14周上半周）

### 十大门派基础武学

| 门派 | 外功 | 内功 | 轻功 |
|:---|:---|:---|:---|
| 少林 | 罗汉拳、般若掌、龙爪手 | 易筋经、洗髓经 | 一苇渡江 |
| 武当 | 太极拳、太极剑 | 纯阳无极功 | 梯云纵 |
| 峨眉 | 峨眉剑法、金顶绵掌 | 峨眉心法 | 金顶轻功 |
| 华山 | 华山剑法、紫霞神功 | 紫霞神功 | 华山身法 |
| 丐帮 | 降龙十八掌、打狗棒法 | 降龙伏虎功 | 逍遥游 |
| 明教 | 乾坤大挪移、圣火令 | 明教心法 | 圣火轻功 |
| 日月神教 | 葵花宝典、吸星大法 | 葵花宝典 | 鬼魅身法 |
| 桃花岛 | 落英神剑掌、玉箫剑法 | 桃花心法 | 桃花影落 |
| 白驼山 | 蛤蟆功、神驼雪山掌 | 蛤蟆功 | 白驼轻功 |
| 星宿派 | 化功大法、三阴蜈蚣爪 | 化功大法 | 星宿身法 |

**任务清单：**
- [ ] 每种武功定义招式列表
- [ ] 招式效果脚本编写
- [ ] 克制关系配置
- [ ] 学习条件设置

**数据格式示例：**
```yaml
# resources/wuxue/shaolin/luohanquan.yaml
kungfu:
  key: luohanquan
  name: 罗汉拳
  type: quan
  menpai: 少林
  description: 少林入门拳法，刚猛有力
  
  requirements:
    menpai: 少林
    level: 1
    max_evil: 0  # 正派武学，邪恶值不能太高
  
  moves:
    - key: luohan_kai_shan
      name: 罗汉开山
      damage: 1.2
      mp_cost: 10
      cooldown: 0
      effect: |
        # 基础伤害招式
        damage = caster.get_attack() * 1.2
        result = MoveEffectResult(
            damage=damage,
            messages=["{caster}使一招罗汉开山，拳风呼啸！"]
        )
    
    - key: luohan_xi_shou
      name: 罗汉献寿
      damage: 1.5
      mp_cost: 20
      cooldown: 3
      effect: |
        # 高伤害招式
        damage = caster.get_attack() * 1.5
        result = MoveEffectResult(
            damage=damage,
            messages=["{caster}双拳齐出，使出罗汉献寿！"]
        )
  
  counters: [jian]  # 克制剑法
  countered_by: [dao, gun]  # 被刀法、棍法克制
```

## 5.3 任务与剧情（第14周下半周）

### 主线任务链

**主线章节：**

1. **初入江湖**（1-10级）
   - 创建角色，选择门派
   - 学习基础武学
   - 首次下山历练

2. **崭露头角**（11-30级）
   - 门派大比
   - 江湖奇遇
   - 首次与魔教交手

3. **名动江湖**（31-60级）
   - 追查阴谋
   - 结识侠侣
   - 大战四大恶人

4. **一代宗师**（61-100级）
   - 正邪决战
   - 武林盟主/魔教教主
   - 多结局分支

**任务清单：**
- [ ] 编写30+主线任务
- [ ] 编写50+支线任务
- [ ] 随机遭遇事件库（20+事件）

**数据格式示例：**
```yaml
# resources/quests/main_chapter1.yaml
quest:
  key: main_c1_q1
  name: 初入师门
  type: main
  chapter: 1
  
  description: |
    你拜入师门已有数日，师父命你去领取入门装备，
    然后到练功场练习基本功。
  
  objectives:
    - type: collect
      target: menpai_uniform
      count: 1
      description: 领取门派服饰
    
    - type: talk
      target: shixiong_li
      description: 向李师兄请教基本功
    
    - type: custom
      description: 在练功场练习至基本功熟练
      check_script: |
        return character.get_skill_level("basic") >= 10
  
  rewards:
    exp: 100
    item: [basic_sword]
    wuxue: [menpai_basic_skill]
  
  next_quest: main_c1_q2
```

## 5.4 NPC数据（第15周）

### 门派NPC

| 门派 | 师父 | 特色NPC |
|:---|:---|:---|
| 少林 | 方丈玄慈 | 扫地僧、觉远 |
| 武当 | 张三丰 | 宋远桥、张翠山 |
| 丐帮 | 帮主 | 传功长老、执法长老 |

**任务清单：**
- [ ] 50+有完整对话的NPC
- [ ] 20+可战斗的NPC
- [ ] 10+商人NPC

**数据格式示例：**
```yaml
# resources/npcs/shaolin.yaml
npcs:
  - key: fangzhang_xuanci
    name: 玄慈方丈
    title: 少林寺方丈
    menpai: 少林
    level: 100
    
    dialogue:
      greeting: 阿弥陀佛，施主有礼了。
      
      topics:
        - keyword: 拜师
          condition: player.menpai is None
          response: |
            我少林乃武林泰山北斗，收徒严格。
            施主若想入我佛门，需先通过考验。
          unlock_quest: shaolin_entrance_test
        
        - keyword: 武功
          response: |
            我少林七十二绝技名震天下，
            但最基础的仍是罗汉拳与易筋经。
    
    schedule:
      - time: "06:00"
        location: shaolin_daxiong
        action: morning_prayer
      - time: "12:00"
        location: shaolin_sengtang
        action: lunch
      - time: "18:00"
        location: shaolin_daxiong
        action: evening_prayer
    
    combat:
      hostile: false
      ai_type: shaolin_master
      skills: [yijinjing, fozhang, longzhuashou]
```

## 阶段五验收标准

- [ ] 可创建角色并选择门派
- [ ] 可完成至少3条主线任务
- [ ] 可学习门派基础武学
- [ ] 可进行NPC对话和战斗


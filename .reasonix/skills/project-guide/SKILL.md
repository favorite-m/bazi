---
name: project-guide
description: 八字命理分析项目使用说明。当用户询问"这个项目怎么用"、"项目介绍"、"如何使用"、"项目概述"、"快速开始"时，加载此 skill 进行回答。
---

# 八字命理分析智能体 — 项目使用说明

> 本项目是一个基于大语言模型（LLM）的**领域专用智能体**，专注于中国传统八字命理学的智能化咨询与分析。

---

## 一、项目架构总览

```
八字/                              ← 项目根目录
├── REASONIX.md                   ← 智能体"宪法"（系统指令）
├── 客户档案/                      ← 用户档案存储
│   ├── 客户档案总目录.md           ← 全局索引（脚本自动维护）
│   └── {用户称呼}/
│       ├── 0-目录.md              ← 子目录与加载策略
│       ├── 0-基础信息.md           ← 基础信息 + YAML 元数据
│       ├── 1-分析记录日志.md        ← 历次分析记录
│       ├── 2-八字分析.md           ← 八字排盘与格局
│       └── ...                    ← 其他分析文件
├── .reasonix/                     ← 技能与工具目录
│   └── skills/
│       ├── cantian-bazi/          ← 八字排盘（TS版，首选）
│       ├── bazi-skill/            ← 八字排盘（Python版，备选）
│       ├── ziwei-doushu/          ← 紫微斗数
│       ├── memory-retrieval/      ← 语义检索
│       ├── documentation-management/ ← 知识管理
│       └── self-improvement/      ← 自我改进
├── .记忆/                          ← 命理知识结晶库
│   ├── 核心_记忆.md               ← 高频核心命理知识
│   └── 当前_记忆.md               ← 近期命理经验
├── .项目进展/                      ← 项目演进记录
│   ├── 核心_项目进展.md            ← 里程碑记录
│   └── 当前_项目进展.md            ← 近期冲刺详情
└── w八字/                         ← 命理参考资料
```

---

## 二、核心工作流（4 步）

### 第 1 步：新对话客户识别

```
1. 读取 客户档案/客户档案总目录.md — 快速扫读判断是否有该客户
2. 如果有 → 进入客户文件夹，读取 0-目录.md + 0-基础信息.md
3. 如果没有 → 询问用户称呼，收集出生信息，新建档案
4. 严禁一次性加载整个客户文件夹的所有文件（按需加载）
```

### 第 2 步：收集出生信息

| 字段 | 必填 | 说明 |
|:----|:----:|:------|
| 称呼 | ✅ | 昵称即可 |
| 出生日期 | ✅ | 公历/农历，默认公历 |
| 出生时刻 | ✅ | 精确到小时和分钟 |
| 出生地点 | ✅ | 省/市，用于真太阳时校正 |
| 性别 | ✅ | |

> 缺时辰 → 默认按子时，告知局限性。未获完整信息前停止分析。

### 第 3 步：排盘计算

**首选（TypeScript 版 — 无需安装依赖）：**
```bash
node .reasonix/skills/cantian-bazi/scripts/buildBaziFromSolar.ts "1997-10-18T09:13:00" 1 2
# 参数: "ISO时间" 性别(1男2女) 排盘模式
```

**备选（Python 版 — 需 pip install）：**
```bash
python .reasonix/skills/bazi-skill/calculate_bazi.py --json '{"year":1997,"month":10,"day":18,"hour":9,"minute":13,"gender":"M","birth_place":"河南"}'
# 或 --pretty 输出彩色终端命盘
```

**紫微斗数：**
```bash
python .reasonix/skills/ziwei-doushu/scripts/ziwei_calc.py --year 1997 --month 10 --day 18 --hour 9 --gender M
```

### 第 4 步：生成报告

输出 6 段式报告模板（参见 `报告模板.md`）：
1. 排盘展示
2. 命局定性（格局、喜忌）
3. 结构拆解（月令、透干、通根、合冲刑害）
4. 大运流年分析
5. 趋吉避凶建议
6. 前事校验引导

---

## 三、客户档案管理

### 目录结构

每个客户一个独立文件夹，文件使用**中文命名 + 数字前缀**：

```
客户档案/{用户称呼}/
├── 0-目录.md          ← 文件清单 + 加载策略
├── 0-基础信息.md       ← 基础信息 + YAML 元数据头
├── 1-分析记录日志.md    ← 历次分析记录
├── 2-八字分析.md       ← 八字排盘与格局
├── 3-紫微斗数.md       ← 紫微命盘
├── 4-事业财运.md       ← 事业财运分析
├── 5-感情婚姻.md       ← 感情婚姻分析
├── 6-生活维度.md       ← 田宅、福德、健康
├── 7-流年预测.md       ← 流年/大运详批
├── 8-特殊记录.md       ← 特殊记录
└── 9-梦境解析.md       ← 梦境解析
```

### 总目录自动更新

新增或删除客户后，运行以下命令更新全局索引：
```bash
python .reasonix/skills/documentation-management/scripts/update_catalog.py
```

### 喜用神修正

当前事校验发现冲突时，使用标准格式记录：
```markdown
## {日期} - 喜用神修正

**旧判定**：喜用神={旧}, 忌神={旧}
**冲突证据**：{年份}年发生{事件}
**新判定**：喜用神={新}, 忌神={新}
**修正依据**：{理由}
```

---

## 四、知识库维护

### 命理知识结晶（.记忆/）

当发现以下情况时，将命理经验写入 `当前_记忆.md`：
- 成功的格局断事模式
- 踩坑后的解决方案
- 搜索获取的 SOTA 命理方案

格式（YAML + Zettelkasten）：
```markdown
## [ID-类别-YYYYMMDD-HHMM]

### Context
- **命盘特征**: ...
- **适用场景**: ...

### The Core
- **实质**: 核心理念
- **断事要点**: 具体规则
```

### 项目进展记录（.项目进展/）

排盘脚本更新、命理体系接入等里程碑完成后写入 `当前_项目进展.md`。

---

## 五、技能路线图

| 技能 | 状态 | 用途 |
|:----|:----:|:-----|
| `cantian-bazi` | ✅ 可用 | 八字排盘（TypeScript，首选） |
| `bazi-skill` | ⚠️ 需装依赖 | 八字排盘（Python，备选） |
| `ziwei-doushu` | ✅ 可用 | 紫微斗数排盘 |
| `memory-retrieval` | ✅ 可用 | 语义检索、客户查询 |
| `documentation-management` | ✅ 可用 | 知识管理、进度记录 |
| `self-improvement` | ✅ 可用 | 错误记录、学习改进 |
| 合婚配对 | ❌ 未实现 | 两人八字对比分析 |
| 择吉日 | ❌ 未实现 | 结婚/搬家择日 |

---

## 六、行为红线

- ❌ 禁止依赖模型自身知识进行排盘计算
- ❌ 禁止提供医疗、法律、财务等确定性建议
- ❌ 禁止分析他人隐私八字
- ❌ 禁止绝对化断语（"一定""绝对"）
- ❌ 禁止一次性加载整个客户文件夹

---

## 七、快速参考

| 操作 | 命令/路径 |
|:----|:---------|
| 八字排盘（TS） | `node .reasonix/skills/cantian-bazi/scripts/buildBaziFromSolar.ts "ISO时间" 性别 模式` |
| 八字排盘（Python） | `python .reasonix/skills/bazi-skill/calculate_bazi.py --json '{...}'` |
| 紫微排盘 | `python .reasonix/skills/ziwei-doushu/scripts/ziwei_calc.py --year ...` |
| 语义检索 | `python .reasonix/skills/memory-retrieval/scripts/memory_retriever.py --query "..."` |
| 更新总目录 | `python .reasonix/skills/documentation-management/scripts/update_catalog.py` |
| 报告模板 | `.reasonix/skills/documentation-management/Reference/报告模板.md` |
| 客户档案规范 | `.reasonix/skills/documentation-management/Reference/客户档案管理规范.md` |

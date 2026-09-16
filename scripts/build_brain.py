#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二大脑骨架生成器 —— 一条命令建好整个文件夹结构。

用法：
    python build_brain.py --path "D:/MyBrain" --name "张三"
    python build_brain.py --path "D:/MyBrain" --dry-run
    python build_brain.py --path "D:/MyBrain" --sections "00_首页导航,01_个人档案,06_行动与复盘,99_临时收件箱"

设计原则：
- 只用标准库，零依赖，任何有 Python 3.8+ 的机器都能跑
- 幂等：已存在的文件不覆盖（安全）
- 每个分区带一份说明文件，用户不会"建了不知道怎么用"
"""

import argparse
import os
import sys
from datetime import date

# ---------------------------------------------------------------- 默认结构

# 分区名 -> (说明文件里的"放什么", "什么时候写", "不要放什么")
SECTIONS = {
    "00_首页导航": (
        "总入口。这里是全库的目录页，每天打开先看这里。",
        "每天开始工作时看一眼；新增分区后回来更新导航。",
        "具体内容。导航页只放链接，不放正文。",
    ),
    "01_个人档案": (
        "你是谁：身份、目标、优势、履历、关键指标。",
        "每学期/每季度更新一次；有重要变化随时补。",
        "临时想法。这里只放已经确认属于你的长期事实。",
    ),
    "02_规则与环境": (
        "外部约束：制度、政策、规则、必须遵守的条款、截止时间。",
        "拿到新的正式文件就归档；规则变化时更新。",
        "你自己的判断。规则原文和你对规则的解读要分开写。",
    ),
    "03_知识与学习": (
        "正在学的东西：课程、读书笔记、技能路线、学习资料。",
        "学完一块就整理一次，别等攒成山。",
        "别人的成套资料（那放 09）。这里是你的学习痕迹。",
    ),
    "04_项目与成果": (
        "做过的事：项目、作品、比赛、可展示的证据。",
        "项目结束时归档；有成果就立刻记，别靠回忆。",
        "进行中的杂事（那放 99）。这里放能拿出手的东西。",
    ),
    "05_机会雷达": (
        "值得抓的机会：申请、比赛、实习、窗口期、截止日期。",
        "每周扫一遍截止日期；过期就删，别留着占地方。",
        "已经错过的机会。留着只会内耗，删掉。",
    ),
    "06_行动与复盘": (
        "日复盘、周复盘、决策记录、认知升级卡。",
        "每天或每周固定一次；复盘必须写下'下次怎么改'。",
        "任务清单（那放 每日任务）。这里放思考，不放待办。",
    ),
    "07_关系与合作": (
        "人：联系人、合作方、师长、同学、重要关系笔记。",
        "认识新的人、有重要对话后记录。",
        "隐私敏感信息。写'怎么合作'，不写'他私生活如何'。",
    ),
    "08_资料库": (
        "沉淀下来的知识卡片、方法论、可复用的框架。",
        "每次复盘后有新结论就沉淀一张卡。",
        "原始素材。这里放加工过的、能直接用的东西。",
    ),
    "09_外部知识库": (
        "别人整理好的成套资料（课程、手册、合集）。",
        "拿到就整体归档，别拆散。",
        "你自己写的东西。这里只放外部来源，注明出处。",
    ),
    "99_临时收件箱": (
        "只放 48 小时内的新东西。进来就得想好去哪。",
        "随时丢进来；每 2~3 天清空一次。",
        "任何你打算长期留的东西。收件箱是走廊，不是房间。",
    ),
}

# 额外的工作流分区（--with-daily 时创建）
DAILY_SECTIONS = {
    "每日任务": (
        "每天的任务清单。固定顺序排列，方便用 0/1 回报法。",
        "每天开工前看一眼；睡前按顺序回 0/1。",
        "想法和思考（那放 06）。这里只放能打勾的事。",
    ),
    "日记": (
        "你自己随手写的东西。低成本输入，不讲究格式。",
        "想写就写，不用每天。",
        "需要 AI 参与分析的大事（那去对话，别写这儿）。",
    ),
    "附件": (
        "图片、PDF、扫描件等非文本文件。",
        "随手丢，按日期或主题分文件夹。",
        "需要长期引用的资料（那放 09）。",
    ),
}

HOME_TEMPLATE = """---
tags: [MOC, 首页]
created: {today}
---

# 🏠 {name}的第二大脑

> 总入口。每天打开先看这里。

## 🧭 快速导航

{nav_table}

## ⚡ 今日聚焦

- [ ] 
- [ ] 
- [ ] 

## 🔄 使用节奏

- **每天**：看「今日聚焦」→ 新东西丢 99 → 睡前清一次
- **每周**：06 里写周复盘，05 里扫一遍机会截止日期
- **每季度**：更新 01（身份与目标）

> 原则：**收件箱只放 48 小时。** 超过就说明你不敢做决定。
"""

PROFILE_TEMPLATE = """---
tags: [个人档案]
created: {today}
---

# 个人档案

> 这里写"你是谁"。每季度更新一次，别频繁改。

## 基本信息

- **称呼**：{name}
- **状态**：
- **所在城市**：

## 目标

### 1~3 年目标
> 

### 关键指标
> 达成与否怎么衡量？（分数 / 收入 / 作品数 / 其他）
> 

## 优势与资源

- 
- 

## 履历与成果

| 时间 | 事项 | 结果 / 证据 |
|---|---|---|
|  |  |  |

## 待补

- [ ] 
- [ ] 
"""

README_IN_SECTION = """# {title}

## 📌 这个分区放什么

{what}

## ⏰ 什么时候往里写

{when}

## 🚫 不要放什么

{notwhat}

---

> 建库日期：{today}
> 说明：这份文件是路标。想清楚"这里放什么"，比建更多文件夹重要。
"""


def build_nav_table(sections):
    """生成首页的导航表格。"""
    rows = ["| 分区 | 用途 | 进入 |", "| ---- | ---- | ---- |"]
    for s in sections:
        if s == "00_首页导航":
            continue
        desc = SECTIONS.get(s, DAILY_SECTIONS.get(s, ("", "", "")))[0]
        # 说明文件在分区内同名，去掉编号前缀
        inner = s.split("_", 1)[-1] if "_" in s else s
        rows.append(f"| {s} | {desc} | [[{s}/{inner}]] |")
    return "\n".join(rows)


def safe_write(path, content):
    """已存在则跳过，不覆盖用户数据。"""
    if os.path.exists(path):
        return "skip"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return "write"


def main():
    ap = argparse.ArgumentParser(
        description="一键生成第二大脑文件夹骨架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--path", required=True, help="库要建在哪里")
    ap.add_argument("--name", default="我", help="怎么称呼你，默认「我」")
    ap.add_argument("--sections", default="", help="自定义分区，逗号分隔。留空用默认全套")
    ap.add_argument("--skip", default="", help="要跳过的分区，逗号分隔")
    ap.add_argument("--with-daily", action="store_true", default=True,
                    help="同时建 每日任务/日记/附件（默认开）")
    ap.add_argument("--no-daily", dest="with_daily", action="store_false",
                    help="不建日常工作流分区")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不创建")
    args = ap.parse_args()

    today = date.today().isoformat()
    root = os.path.abspath(args.path)

    # 组装分区清单
    if args.sections.strip():
        sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    else:
        sections = list(SECTIONS.keys())
        if args.with_daily:
            sections += list(DAILY_SECTIONS.keys())

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    sections = [s for s in sections if s not in skip]

    if not sections:
        print("错误：分区清单为空。", file=sys.stderr)
        return 1

    # 预演：只打印将要创建的东西
    if args.dry_run:
        print(f"[预演] 库位置：{root}")
        print(f"[预演] 称呼：{args.name}")
        print(f"[预演] 将创建 {len(sections)} 个分区：")
        for s in sections:
            print(f"    {s}/")
        print("[预演] 外加 00_首页导航/HOME.md 和 01 里的个人档案.md")
        print("\n去掉 --dry-run 就会真的建。")
        return 0

    # 真正创建
    os.makedirs(root, exist_ok=True)
    created_dirs, created_files, skipped = 0, 0, 0

    for s in sections:
        sdir = os.path.join(root, s)
        os.makedirs(sdir, exist_ok=True)
        created_dirs += 1

        info = SECTIONS.get(s) or DAILY_SECTIONS.get(s)
        if not info:
            continue

        # 分区内的说明文件，去掉编号前缀当文件名
        inner = s.split("_", 1)[-1] if "_" in s else s
        fpath = os.path.join(sdir, f"{inner}.md")
        body = README_IN_SECTION.format(
            title=inner, what=info[0], when=info[1], notwhat=info[2], today=today
        )
        result = safe_write(fpath, body)
        created_files += result == "write"
        skipped += result == "skip"

    # 首页
    home_dir = os.path.join(root, "00_首页导航")
    os.makedirs(home_dir, exist_ok=True)
    result = safe_write(
        os.path.join(home_dir, "HOME.md"),
        HOME_TEMPLATE.format(today=today, name=args.name, nav_table=build_nav_table(sections)),
    )
    created_files += result == "write"
    skipped += result == "skip"

    # 个人档案（只填用户给过的信息）
    profile_dir = os.path.join(root, "01_个人档案")
    if os.path.isdir(profile_dir):
        result = safe_write(
            os.path.join(profile_dir, "个人档案.md"),
            PROFILE_TEMPLATE.format(today=today, name=args.name),
        )
        created_files += result == "write"
        skipped += result == "skip"

    # 汇报
    print(f"✅ 第二大脑已建好：{root}")
    print(f"   分区 {created_dirs} 个，新建文件 {created_files} 个"
          + (f"，跳过已存在 {skipped} 个" if skipped else ""))
    print("\n目录结构：")
    for s in sections:
        print(f"  ├── {s}/")
    print("\n下一步：打开 00_首页导航/HOME.md，填上今天的三个重点。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

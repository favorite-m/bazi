"""
# 客户档案总目录自动更新脚本 (Catalog Auto-Updater)
# 功能：扫描 /客户档案/ 下所有用户文件夹，读取 0-基础信息.md 的 YAML 元数据，
#       自动生成 /客户档案/客户档案总目录.md
# 用法：python update_catalog.py
# 依赖：pyyaml (pip install pyyaml)
"""

import os
import sys
import re
import datetime
from pathlib import Path

# Configuration — auto-detect project root by looking for REASONIX.md
def find_project_root(start_path):
    """Walk up from start_path until we find REASONIX.md (project root marker)."""
    current = Path(start_path).resolve()
    for _ in range(10):  # max 10 levels up
        if (current / "REASONIX.md").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: use script location and go up 5 levels
    return Path(start_path).resolve().parent.parent.parent.parent.parent

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root(SCRIPT_DIR)
CUSTOMER_DIR = PROJECT_ROOT / "客户档案"
CATALOG_FILE = CUSTOMER_DIR / "客户档案总目录.md"

def parse_yaml_header(filepath):
    """Parse YAML front matter from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    # Extract YAML between --- markers
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None

    yaml_text = m.group(1)
    # Simple key-value parsing (no pyyaml dependency needed for basic fields)
    data = {}
    for line in yaml_text.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            data[key] = val
    return data


def count_analysis_logs(user_dir):
    """Count analysis log entries in 1-分析记录日志.md."""
    log_file = user_dir / "1-分析记录日志.md"
    if not log_file.exists():
        return 0
    try:
        content = log_file.read_text(encoding="utf-8")
        # Count ## headers as entries
        headers = re.findall(r'^##\s+\d{4}-\d{2}-\d{2}', content, re.MULTILINE)
        return len(headers)
    except Exception:
        return 0


def get_last_updated(user_dir):
    """Find the most recent update date from 1-分析记录日志.md or 0-基础信息.md."""
    # Check 1-分析记录日志.md for latest entry
    log_file = user_dir / "1-分析记录日志.md"
    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8")
            dates = re.findall(r'##\s+(\d{4}-\d{2}-\d{2})', content)
            if dates:
                return max(dates)
        except Exception:
            pass
    return "—"


def scan_customers():
    """Scan /客户档案/ directory and collect metadata."""
    if not CUSTOMER_DIR.exists():
        print(f"错误：客户档案目录不存在 - {CUSTOMER_DIR}")
        return []

    customers = []
    for item in sorted(CUSTOMER_DIR.iterdir()):
        if not item.is_dir():
            continue
        profile_file = item / "0-基础信息.md"
        if not profile_file.exists():
            continue

        meta = parse_yaml_header(profile_file)
        if meta is None:
            continue

        name = meta.get("name", item.name)
        slug = meta.get("slug", item.name)
        gender = "男" if meta.get("gender") == "M" else "女" if meta.get("gender") == "F" else "?"
        
        # Extract day master (日主) and pattern (格局) from tags or content
        day_master = "—"
        pattern = "—"
        tags = meta.get("tags", "")
        if tags:
            # Try to extract day master from tags (first tag after '客户')
            tag_list = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
            # Look for day master (癸水, 甲木, etc.)
            dm_pattern = re.compile(r'[甲乙丙丁戊己庚辛壬癸][木火土金水]')
            for t in tag_list:
                if dm_pattern.match(t):
                    day_master = t
                    break
        
        # Read profile content for day master and pattern
        try:
            content = profile_file.read_text(encoding="utf-8")
            # Find 日主
            dm_m = re.search(r'\|\s*\*\*日主\*\*\s*\|\s*(\S+)', content)
            if dm_m:
                day_master = dm_m.group(1)
            # Find 格局
            p_m = re.search(r'\|\s*\*\*格局\*\*\s*\|\s*(\S+)', content)
            if p_m:
                pattern = p_m.group(1)
        except Exception:
            pass

        analysis_count = count_analysis_logs(item)
        last_updated = get_last_updated(item)
        dir_name = item.name

        customers.append({
            "name": name,
            "dir": dir_name,
            "day_master": day_master,
            "pattern": pattern,
            "analysis_count": analysis_count,
            "last_updated": last_updated,
        })

    return customers


def generate_catalog(customers):
    """Generate the customer catalog markdown content."""
    now = datetime.date.today().strftime("%Y-%m-%d")
    
    lines = [
        "# 客户档案总目录",
        "",
        f"> 本文件由 `update_catalog.py` 脚本自动维护更新",
        f"> 最后更新：{now}",
        "",
        "---",
        "",
        "## 客户清单",
        "",
        "| 序号 | 用户 | 文件夹 | 日主 | 格局 | 分析次数 | 最近更新 | 操作指引 |",
        "|:----:|:----|:------|:----:|:----:|:--------:|:--------:|:---------|",
    ]

    for i, c in enumerate(customers, 1):
        lines.append(
            f"| {i} | {c['name']} | [{c['dir']}](./{c['dir']}/) | {c['day_master']} | {c['pattern']} | {c['analysis_count']} | {c['last_updated']} | [查看档案](./{c['dir']}/0-目录.md) |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 快速检索",
        "",
        "如需查找特定用户，调用 `memory-retriever.py`：",
        "```bash",
        'python "$SCRIPT_PATH" --query "客户名 命盘" --target-dir /客户档案',
        "```",
        "",
        "---",
        "",
        f"## 统计",
        "",
        f"- **用户总数**：{len(customers)}",
    ])

    return "\n".join(lines) + "\n"


def main():
    print(f"扫描目录：{CUSTOMER_DIR}")
    customers = scan_customers()
    
    if not customers:
        print("未找到任何客户档案")
        # Write empty catalog
        content = generate_catalog([])
    else:
        print(f"找到 {len(customers)} 个客户：")
        for c in customers:
            print(f"  - {c['name']} ({c['dir']}/): 日主={c['day_master']}, 格局={c['pattern']}, 分析{c['analysis_count']}次")
        content = generate_catalog(customers)

    CATALOG_FILE.write_text(content, encoding="utf-8")
    print(f"\n总目录已更新：{CATALOG_FILE}")


if __name__ == "__main__":
    main()

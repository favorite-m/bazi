'''
创建初始化的文档
'''
import os
from pathlib import Path

def create_file_if_missing(path: Path, initial_content=""):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(initial_content, encoding="utf-8")
        print(f"[Init] Created {path}")
    else:
        print(f"[Init] {path} already exists. Skipping.")

def init_memory_spaces(root_dir_str):
    root_dir = Path(root_dir_str).resolve()
    print(f"Initializing Flat-Tiered Memory Architecture in {root_dir}")

    # 1. Progress Space (.项目进展)
    prog_dir = root_dir / ".项目进展"
    prog_archive = prog_dir / "存档"
    
    prog_core = prog_dir / "核心_项目进展.md"
    prog_curr = prog_dir / "当前_项目进展.md"
    prog_core_idx = prog_dir / "核心_项目进展_index.md"
    prog_curr_idx = prog_dir / "当前_项目进展_index.md"
    prog_arch_idx = prog_archive / "历史_项目进展_index.md"

    create_file_if_missing(prog_core, "# 核心架构演进节点\n\n> 存储当前系统长效存续的核心节点变动记录。\n")
    create_file_if_missing(prog_curr, "# 当前进度缓冲区块\n\n> 记录最近 2-5 天内的冲刺详情。\n")
    create_file_if_missing(prog_core_idx, "# 核心项目进展 全景索引地图 (Omni-Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")
    create_file_if_missing(prog_curr_idx, "# 当前项目进展 全景索引地图 (Omni-Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")
    create_file_if_missing(prog_arch_idx, "# 冷数据存档索引 (Archive Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")

    # 2. Knowledge Space (.记忆)
    mem_dir = root_dir / ".记忆"
    mem_archive = mem_dir / "存档"
    
    mem_core = mem_dir / "核心_记忆.md"
    mem_curr = mem_dir / "当前_记忆.md"
    mem_core_idx = mem_dir / "核心_记忆_index.md"
    mem_curr_idx = mem_dir / "当前_记忆_index.md"
    mem_arch_idx = mem_archive / "历史_记忆_index.md"

    create_file_if_missing(mem_core, "# 核心记忆节点\n\n> 存储最具跨模块指导意义的高频知识点。\n")
    create_file_if_missing(mem_curr, "# 当前结晶缓冲区块\n\n> 最新抓取或定义的经验记录。\n")
    create_file_if_missing(mem_core_idx, "# 核心记忆 全景索引地图 (Omni-Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")
    create_file_if_missing(mem_curr_idx, "# 当前记忆 全景索引地图 (Omni-Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")
    create_file_if_missing(mem_arch_idx, "# 冷数据存档索引 (Archive Index)\n\n| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |\n|---|---|---|\n")

    print(f"\n[Success] Memory and Progress spaces initialized according to the SOTA YAML-Infused schema.")

if __name__ == "__main__":
    # If run in the root of the repo
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    init_memory_spaces(target)

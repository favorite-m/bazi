# -*- coding: utf-8 -*-
r"""用法: python memory_manager.py <该空间下任意.md>  一般传 当前_记忆.md 或 当前_项目进展.md
依赖 pyyaml。路径含「.记忆」→记忆空间；含「项目进展」→进展空间；否则按记忆。
作用: 超限归档、核心 [OBSOLETE] 剔除、生成/更新 核心/当前/存档 的 *_index.md。

举例：
更新项目进展 python ".\skills\documentation-management\scripts\memory_manager.py"  ".trae\.项目进展\当前_项目进展.md"
更新记忆 python ".\skills\documentation-management\scripts\memory_manager.py"  ".trae\.记忆\当前_记忆.md"
"""

import os
import sys
import re
import yaml
import datetime
from pathlib import Path

# Configuration
MAX_LINES = 500
MAX_ITEMS = 30
MAX_SLUG_LEN = 80
MAX_SLUG_DEDUP = 99

# 与 Reference/项目进展管理规则.md、记忆管理规则.md 一致；扩展类型或基建标题时在此维护
KNOWN_TYPES = frozenset({
    "MILESTONE", "FEATURE", "REFACTOR", "HOTFIX", "PATTERN", "CONSTRAINT",
    "ANTI-PATTERN", "RESOLVED", "KNOWLEDGE", "OPTIMIZATION", "ARCHITECTURE", "HEURISTIC",
})
INFRA_KEYWORDS = ("索引", "总结", "看板", "Map", "关键文件快照", "对话总结")
DATE_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(-\d{4})?$|^\d{8}(-\d{4})?$")
PLACEHOLDER_EMPTY = "—"

class MemoryManager:
    """
    Intelligent manager for Flat-Tiered Memory Architecture.
    Handles both Knowledge Space (.记忆) and Progress Space (.项目进展).
    Features:
    - YAML-Infused Parsing: Extracts metadata directly from `yaml` codeblocks for 100% robust reading.
    - Auto-Compaction: Moves old items to archive chunks when limits are reached.
    - Milestone Promotion: Promotes MILESTONE/REFACTOR to Core Progress.
    - Tombstone Eviction: Detects and physically removes [OBSOLETE] items from Core.
    - Global Indexing: Generates high-density Omni-Index tables.
    """

    def __init__(self, target_file):
        self.target_path = Path(target_file).resolve()
        self.target_dir = self.target_path.parent
        self.is_memory = ".记忆" in self.target_dir.parts
        self.is_progress = "项目进展" in self.target_dir.parts or ".项目进展" in self.target_dir.parts
        
        # Determine specific paths
        self.dir_name = self.target_dir.name
        self.core_file = self.target_dir / f"核心_{self.dir_name.replace('.', '')}.md"
        self.current_file = self.target_dir / f"当前_{self.dir_name.replace('.', '')}.md"
        self.archive_dir = self.target_dir / "存档"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        print(f"[MemoryManager] Starting YAML-Infused processing for {self.target_path.name}")
        
        if not self.target_path.exists():
            print(f"[MemoryManager] File {self.target_path} does not exist. Initializing...")
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            self.target_path.touch()
        
        if self.is_progress:
            self.process_progress_space()
        elif self.is_memory:
            self.process_memory_space()
        else:
            print(f"[MemoryManager] Target {self.target_path} is neither in .记忆 nor .项目进展. Assuming Memory fallback...")
            self.process_memory_space()
            
        # Re-generate indexes using YAML extraction
        self.generate_indexes()
        print("[MemoryManager] Operations completed.")

    # ------------------ PROGRESS SPACE ------------------
    def process_progress_space(self):
        # 1. Promote & Compact '当前'
        if self.current_file.exists():
            content = self.current_file.read_text(encoding="utf-8")
            items = self._parse_items(content)
            
            # Promote Core Items
            core_content = ""
            if self.core_file.exists():
                 core_content = self.core_file.read_text(encoding="utf-8")
            
            core_items = self._parse_items(core_content) if core_content else []
            core_ids = {self._extract_metadata(item).get('id', 'N/A'): True for item in core_items}
            
            promoted_items = []
            active_items = []
            archived_items = []
            
            for item in items:
                meta = self._extract_metadata(item)
                item_id = meta.get("id") or ""
                m_type = str(meta.get("type") or "").upper()
                m_status = str(meta.get('status', '')).upper()
                
                # Check Promotion
                is_milestone = "MILESTONE" in m_type or "REFACTOR" in m_type
                if is_milestone and item_id not in core_ids:
                    promoted_items.append(item)
                    core_ids[item_id] = True
                
                # Partition Active vs Archived
                is_obsolete = "OBSOLETE" in m_status
                is_completed = "已完成" in m_status or "[X]" in m_status
                
                if is_obsolete or is_completed:
                    archived_items.append(item)
                else:
                    active_items.append(item)
                    
            lines_count = len(content.splitlines())
            if lines_count > MAX_LINES or len(items) > MAX_ITEMS:
                print(f"[MemoryManager] '当前' file size exceeds limit ({lines_count} lines, {len(items)} items). Archiving...")
                self._archive_items(archived_items, prefix="历史_项目进展_chunk")
                self._rewrite_file(self.current_file, active_items, "当前项目进展记录")
            
            # Write Promoted + Evict Core
            if promoted_items or self.core_file.exists():
                all_core_items = []
                # Don't duplicate
                seen = set()
                for c_item in core_items + promoted_items:
                    c_id = self._extract_metadata(c_item).get('id', '')
                    if c_id not in seen:
                        all_core_items.append(c_item)
                        seen.add(c_id)

                valid_core_items = []
                evicted_items = []
                
                for item in all_core_items:
                    meta = self._extract_metadata(item)
                    m_status = str(meta.get('status', '')).upper()
                    if "OBSOLETE" in m_status:
                        evicted_items.append(item)
                    else:
                        valid_core_items.append(item)
                
                if evicted_items:
                    print(f"[MemoryManager] Evicted {len(evicted_items)} [OBSOLETE] items from Core.")
                    self._archive_items(evicted_items, prefix="历史_历史核心淘汰区")
                
                self._rewrite_file(self.core_file, valid_core_items, "核心架构演进节点")

    # ------------------ MEMORY SPACE ------------------
    def process_memory_space(self):
        # 1. Compact '当前'
        if self.current_file.exists():
            content = self.current_file.read_text(encoding="utf-8")
            items = self._parse_items(content)
            
            lines_count = len(content.splitlines())
            if lines_count > MAX_LINES or len(items) > MAX_ITEMS:
                print(f"[MemoryManager] '当前' file size exceeds limit ({lines_count} lines, {len(items)} items). Compacting...")
                # Keep the last 5 active, archive the rest
                keep_items = items[-5:] if len(items) >= 5 else items
                archived_items = items[:-5] if len(items) >= 5 else []
                
                if archived_items:
                    self._archive_items(archived_items, prefix="历史_记忆_chunk")
                
                self._rewrite_file(self.current_file, keep_items, "当前结晶缓冲区块")

        # Handle Core Memory OBSOLETE eviction
        if self.core_file.exists():
            core_content = self.core_file.read_text(encoding="utf-8")
            core_items = self._parse_items(core_content)
            valid_core = []
            evicted = []
            for item in core_items:
                meta = self._extract_metadata(item)
                m_status = str(meta.get('status', '')).upper()
                if "OBSOLETE" in m_status:
                    evicted.append(item)
                else:
                    valid_core.append(item)
                    
            if evicted:
                print(f"[MemoryManager] Evicted {len(evicted)} [OBSOLETE] items from Core Memory.")
                self._archive_items(evicted, prefix="历史_记忆_chunk")
                self._rewrite_file(self.core_file, valid_core, "核心记忆节点")

    # ------------------ YAML-INFUSED PARSERS ------------------
    def _parse_items(self, content):
        """Splits content by ## headers."""
        header_regex = r'(?m)^## .*'
        parts = re.split(header_regex, content)
        matches = re.findall(header_regex, content)
        items = []
        for i, match in enumerate(matches):
             items.append(match + parts[i+1])
        return items

    def _has_yaml_block(self, text):
        """是否存在 ```yaml 代码块"""
        return bool(re.search(r"```yaml\n.*?\n```", text, re.DOTALL))

    def _has_progress_fingerprint(self, text):
        """正文是否含演进指纹：### Context / The Core 或任务列表 [ ] / [x]"""
        if re.search(r"###\s+(?:1\.\s+)?(?:Context|The Core)", text):
            return True
        if re.search(r"\[\s*[xX]?\s*\]", text):
            return True
        return False

    def _is_infrastructure_block(self, item_str):
        """是否为文档基建块（不写入索引）：标题关键词或纯数字编号且无 YAML/无演进指纹"""
        if self._has_yaml_block(item_str):
            return False
        first_line = item_str.split("\n")[0] if item_str else ""
        title_after_hash = re.sub(r"^##\s+", "", first_line).strip()
        has_infra_keyword = any(kw in title_after_hash for kw in INFRA_KEYWORDS)
        is_numbered_only = bool(re.match(r"^\d+\.\s+", title_after_hash))
        if not has_infra_keyword and not is_numbered_only:
            return False
        if self._has_progress_fingerprint(item_str):
            return False
        bracket_match = re.match(r"^##\s+.*?\[([^\]]+)\].*$", first_line)
        if bracket_match and bracket_match.group(1).strip().upper() in KNOWN_TYPES:
            return False
        return True

    def _title_to_slug(self, title, seen_ids=None):
        """从标题生成唯一 slug：去编号前缀、保留中英数字连字符，空格/标点替为 -"""
        seen_ids = seen_ids or set()
        t = re.sub(r"^\d+\.\s*", "", title.strip())
        t = re.sub(r"[^\w\s\u4e00-\u9fff\-]", " ", t)
        t = re.sub(r"\s+", "-", t.strip()).strip("-")
        if not t:
            t = "unnamed"
        slug = t[:MAX_SLUG_LEN]
        if slug in seen_ids:
            for i in range(1, MAX_SLUG_DEDUP + 1):
                candidate = f"{slug}-{i}"
                if candidate not in seen_ids:
                    slug = candidate
                    break
        return slug

    def _extract_metadata(self, item_str):
        """
        解析 H2 标题与 YAML 块，返回 id/title/type/status/tags。无 UNKNOWN：从严到宽 ID 降级，type/status 兜底为 —。
        """
        meta = {}
        lines = item_str.splitlines()
        first_line = lines[0] if lines else ""
        header_match = re.match(r"^##\s+\[(.*?)\](.*)$", first_line.strip())

        if header_match:
            bracket = header_match.group(1).strip()
            title_part = header_match.group(2).strip()
            if not title_part:
                title_part = re.sub(r"^##\s+\[[^\]]+\]\s*", "", first_line).strip()
            if not title_part:
                title_part = "Unnamed"

            if DATE_ID_RE.match(bracket):
                meta["id"] = bracket
                meta["title"] = title_part
            elif bracket.upper() in KNOWN_TYPES:
                meta["type"] = bracket.upper()
                meta["id"] = self._title_to_slug(title_part)
                meta["title"] = title_part
            else:
                meta["id"] = bracket
                meta["title"] = title_part
        else:
            raw_title = re.sub(r"^##\s+", "", first_line).strip() or "Unnamed"
            meta["id"] = self._title_to_slug(raw_title)
            meta["title"] = raw_title

        yaml_match = re.search(r"```yaml\n(.*?)\n```", item_str, re.DOTALL)
        if yaml_match:
            try:
                parsed = yaml.safe_load(yaml_match.group(1)) or {}
                if isinstance(parsed, dict):
                    meta.update(parsed)
            except yaml.YAMLError as e:
                print(f"[MemoryManager] YAML Parse error for ID {meta.get('id', '')}: {e}")

        if not meta.get("type"):
            meta["type"] = PLACEHOLDER_EMPTY
        if not meta.get("status"):
            meta["status"] = PLACEHOLDER_EMPTY
        return meta

    # ------------------ UTILS ------------------
    def _archive_items(self, items, prefix):
        if not items: return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.md"
        filepath = self.archive_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Archive Chunk - {ts}\n\n")
            f.write("".join(items))
        print(f"[MemoryManager] Archived {len(items)} items to {filename}")

    def _rewrite_file(self, path, items, title):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write("".join(items))

    # ------------------ INDEXING ------------------
    def generate_indexes(self):
        """Generates semantic index Omni-Dashboards utilizing the YAML metadata."""
        self._generate_index_file(self.core_file, self.target_dir / f"核心_{self.dir_name.replace('.','')}_index.md")
        self._generate_index_file(self.current_file, self.target_dir / f"当前_{self.dir_name.replace('.','')}_index.md")
        
        # Archive index
        archive_index_path = self.archive_dir / f"历史_{self.dir_name.replace('.','')}_index.md"
        archive_files = list(self.archive_dir.glob("*.md"))
        
        all_archive_items = []
        for arch_file in archive_files:
            if arch_file.name == archive_index_path.name: continue
            content = arch_file.read_text(encoding="utf-8")
            items = self._parse_items(content)
            for item in items:
                all_archive_items.append((arch_file.name, item))
                
        self._write_index_table(archive_index_path, all_archive_items, "冷数据存档索引 (Archive Index)")

    def _generate_index_file(self, source_file, index_file):
        if not source_file.exists(): return
        content = source_file.read_text(encoding="utf-8")
        items = self._parse_items(content)
        items_with_path = [(source_file.name, item) for item in items]
        self._write_index_table(index_file, items_with_path, f"{source_file.stem} 全景索引地图 (Omni-Index)")

    def _write_index_table(self, index_file, items_with_path, title):
        indexable = [(fname, item) for fname, item in items_with_path if not self._is_infrastructure_block(item)]
        lines = []
        lines.append(f"# {title}")
        lines.append("> 本表由 `memory_manager.py` 自动化聚合。专为 `memory-retrieval` 技能与人类开发者优化的语义俯瞰视窗。\n")
        lines.append("| 核心标识 (ID / Type / Status) | 摘要速览 (Title & Tags) | 导航映射 (Deep Link) |")
        lines.append("|---|---|---|")

        for filename, item in indexable:
            meta = self._extract_metadata(item)
            i_id = meta.get("id") or PLACEHOLDER_EMPTY
            i_type = meta.get("type") or PLACEHOLDER_EMPTY
            i_type = i_type if isinstance(i_type, str) else str(i_type)
            i_type = i_type.upper() if i_type != PLACEHOLDER_EMPTY else i_type
            i_status = meta.get("status") or PLACEHOLDER_EMPTY
            i_title = (meta.get("title") or "Unnamed").replace(" ", "")
            raw_tags = meta.get("tags", "")
            i_tags = ", ".join([str(t) for t in raw_tags]) if isinstance(raw_tags, list) else str(raw_tags)
            col1 = f"**[{i_id}]**<br/>`[{i_type}]`<br/>*[{i_status}]*"
            col2 = f"**{i_title}**<br/>️ `{i_tags}`"
            anchor = str(i_id).lower().replace(".", "").replace(" ", "-")
            col3 = f" [进入关联切片](./{filename}#{anchor})"
            lines.append(f"| {col1} | {col2} | {col3} |")

        index_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"[MemoryManager] Re-built index at {index_file.name} with {len(indexable)} entries.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python memory_manager.py <target_md_file>")
        sys.exit(1)
    
    target = sys.argv[1]
    manager = MemoryManager(target)
    manager.run()

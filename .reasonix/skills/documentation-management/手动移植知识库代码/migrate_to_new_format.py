
'''
将老格式的数据库进行移植
'''
import os
import sys
import re
from pathlib import Path

def migrate_memory_format(test_dir):
    old_file = test_dir / "原始_记忆.md"
    new_file = test_dir / "migrated_当前_记忆.md"

    if not old_file.exists():
        print(f"Skipping memory migration, {old_file} not found.")
        return

    content = old_file.read_text(encoding="utf-8")
    parts = re.split(r'(?m)^ID:\s+', content)
    
    if len(parts) < 2:
        print("No items found to migrate in memory.")
        return

    new_items = []
    
    for part in parts[1:]:
        lines = part.strip().splitlines()
        if not lines: continue
        
        item_id = lines[0].strip()
        title = ""
        category = "UNKNOWN"
        version = "2026-01-01"
        confidence = 0.5
        keywords = []
        
        rest_of_body = []
        for line in lines[1:]:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("CATEGORY:"):
                category = line.replace("CATEGORY:", "").strip()
            elif line.startswith("VERSION:"):
                version = line.replace("VERSION:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try: confidence = float(line.replace("CONFIDENCE:", "").strip())
                except: pass
            elif line.startswith("VITALITY:"):
                continue  # skip old vitality
            elif "- **关键词**:" in line or "- **Keywords**:" in line:
                kw_str = line.split(":", 1)[1].strip()
                keywords = [k.strip() for k in kw_str.split(",")]
                rest_of_body.append(line)
            else:
                rest_of_body.append(line)
                
        # Format to new format
        new_item = []
        # Format: [ID-项目名称-类别-YYYYMMDD-HHMM]
        # Memory ID often looks like "CONSTRAINT_LED_PIN_48". We will prefix with "ID-" and append "-YYYYMMDD-HHMM" if valid version.
        smart_id_parts = [item_id]
        if version and version.count("-") >= 2:
            smart_id_parts.append(version.replace(" ", "-").replace(":", ""))
        smart_id = "-".join(smart_id_parts)
        
        new_item.append(f"##  [{smart_id}] {title}")
        new_item.append("```yaml")
        new_item.append(f"type: {category}")
        new_item.append(f"status: {confidence}")
        new_item.append(f"vitality: {{ usage: 0, last_ref: \"2026-02-26\" }}")
        
        quoted_tags = []
        for tag in keywords:
            escaped = tag.replace("'", "''")
            quoted_tags.append(f"'{escaped}'")

        new_item.append(f"tags: [{', '.join(quoted_tags)}]")
        new_item.append("```")
        new_item.append("\n### 1. Context (上下文与边界)")
        new_item.append("* **Files Affected**: `[]`")
        new_item.append("* **Local Modules**: `[]`")
        new_item.append(f"* **背景**: \n" + "\n".join(rest_of_body).strip())
        new_item.append("\n### 2. The Core (核心结晶与实现)")
        new_item.append("* **实质**: \n")
        new_item.append("* **实现**: \n")
        new_item.append("\n### 3. Constraints & Defense (限制与防御)")
        new_item.append("* **限制**: \n")
        new_item.append("* **操作指令**: \n")
        new_item.append("\n")
        new_items.append("\n".join(new_item))

    with open(new_file, "w", encoding="utf-8") as f:
        f.write("# 迁移的记忆缓冲 (Migrated Memory Chunk)\n\n")
        f.write("\n".join(new_items))
    print(f"Migrated memory to {new_file.name}")

def migrate_progress_format(test_dir):
    old_file = test_dir / "原始_项目进展.md"
    new_file = test_dir / "migrated_当前_项目进展.md"

    if not old_file.exists():
        print(f"Skipping progress migration, {old_file} not found.")
        return

    content = old_file.read_text(encoding="utf-8")
    parts = re.split(r'(?m)^### <a id=".*?"></a>\s*.*?Record:', content)
    
    if len(parts) < 2:
        print("No items found to migrate in progress.")
        return

    new_items = []
    
    for part in parts[1:]:
        lines = part.strip().splitlines()
        if not lines: continue
        
        first_line = lines[0].strip()
        m = re.match(r'(.*?)\[(.*?)\]$', first_line)
        if m:
            title = m.group(1).strip()
            p_type = m.group(2).strip().upper()
        else:
            title = first_line
            p_type = "UNKNOWN"
            
        timestamp = ""
        files_affected = ""
        status = "已完成" # default
        
        summary = []
        context = []
        todos = []
        tags = []
        
        current_section = None
        
        for line in lines[1:]:
            if line.startswith("- **Timestamp:**"):
                timestamp = line.replace("- **Timestamp:**", "").strip()
            elif line.startswith("- **Files Affected:**"):
                files_affected = line.replace("- **Files Affected:**", "").strip()
                # Use files affected as rough tags
                raw_tags = files_affected.replace("`", "").split(",")
                tags = [t.strip().split("/")[-1] for t in raw_tags if t.strip()] # just get basename
            elif line.startswith("- **Summary:**"):
                summary.append(line.replace("- **Summary:**", "").strip())
                current_section = "summary"
            elif line.startswith("- **Context:**"):
                current_section = "context"
            elif line.startswith("- **Status:**"):
                current_section = "status"
            elif line.startswith("- **TODO:**"):
                todos.append(line.replace("- **TODO:**", "").strip())
                current_section = "todo"
            elif line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"):
                if current_section == "status":
                    if "- [x]" in line:
                        status = "已完成"
                    elif "- [ ]" in line:
                        status = "推进中"
                else:
                    if current_section == "context": context.append(line)
            else:
                if current_section == "summary": summary.append(line)
                elif current_section == "context": context.append(line)
                elif current_section == "todo": todos.append(line)

        # format
        new_item = []
        pid = timestamp.replace(" ", "-").replace(":", "") if timestamp else ""
        # Format: [ID-项目名称-类别-YYYYMMDD-HHMM]
        # Since project name is unknown, we leave it blank or omit. 
        # But user wants intelligent parsing: if it's progress, maybe ID is just the timestamp.
        # Let's construct a smart ID
        smart_id_parts = []
        if pid: smart_id_parts.append(pid)
        else: smart_id_parts.append("UNKNOWN")
        smart_id = "-".join(smart_id_parts)

        new_item.append(f"##  [{smart_id}] {title}")
        new_item.append("```yaml")
        new_item.append(f"type: {p_type}")
        new_item.append(f"vitality: {{ usage: 0, last_ref: \"2026-02-26\" }}")
        new_item.append(f"status: {status}")
        
        quoted_tags = []
        for tag in tags:
            escaped = tag.replace("'", "''")
            quoted_tags.append(f"'{escaped}'")

        new_item.append(f"tags: [{', '.join(quoted_tags)}]")
        new_item.append("```")
        new_item.append("\n### 1. Context (多维上下文)")
        new_item.append(f"* **Files Affected**: `{files_affected if files_affected else '[]'}`")
        new_item.append("* **Local Modules**: `[]`")
        new_item.append("* **Input/Output**: `[]`")
        new_item.append(f"* **背景**: \n" + "\n".join(context).strip())
        new_item.append("\n### 2. The Core (动机与演进)")
        new_item.append("* **Summary**: \n" + "\n".join(summary).strip())
        new_item.append("* **实质细节**: ")
        new_item.append("\n### 3. Status & Next (状态与遗留)")
        new_item.append("* **Status**: ")
        if status == "已完成":
            new_item.append("  - [x] 核心功能完备，可交付。")
        else:
            new_item.append("  - [ ] 逻辑已跑通，待补充边界处理。")
        new_item.append("* **TODO**: " + ("\n    * [ ] " + "\n    * [ ] ".join(todos).strip() if todos else "无"))
        new_item.append("\n")
        new_items.append("\n".join(new_item))

    with open(new_file, "w", encoding="utf-8") as f:
        f.write("# 迁移的项目进展 (Migrated Progress Chunk)\n\n")
        f.write("\n".join(new_items))
    print(f"Migrated progress to {new_file.name}")

if __name__ == "__main__":
    test_dir = Path(r"C:\Users\MY\Desktop\face_tracking_robot\brain_system\.docs").resolve()
    print(f"Migrating files in {test_dir} to YAML-Infused format...")
    migrate_memory_format(test_dir)
    migrate_progress_format(test_dir)
    print("Done.")

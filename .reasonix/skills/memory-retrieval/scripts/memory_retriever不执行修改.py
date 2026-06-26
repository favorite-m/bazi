"""
# AI Memory Retriever - CLI Interface (V4.1.0)
# Description: 模块化、多领域记忆检索器。支持自动领域扫描、二级混合检索（Level 1 索引扫描 + Level 2 语义 RAG）。
# Project: 记忆管理 (Memory Management System)
# Repository: https://github.com/architect/memory-retrieval
#
# Usage (使用说明):
# 1. 基础查询 (自动发现): python memory_retriever.py "查询内容"
# 2. 指定范围: python memory_retriever.py '{"query": "内容", "target_dirs": [".记忆"]}'
# 3. 强制深度检索: python memory_retriever.py '{"query": "内容", "level": 3}'
# 4. 指定工作空间根目录: python memory_retriever.py '{"query": "内容", "root": "C:/path/to/workspace"}'
# 
# Features:
# - Workspace Auto-Discovery (SOTA 4.2.0): 同时从 CWD 和脚本路径向上递归发现 .记忆 或 .项目进展 根文件夹。
# - Dual-Level Search: 优先快速索引扫描，补充深度语义向量匹配。
# - SOTA Consistency: 异步 FAISS 索引更新，提供最终一致性体验。
"""
import sys
import io
import json
import argparse
import os
import re
import datetime
from pathlib import Path

# [SOTA] Force UTF-8 for stdout/stderr on Windows.
# Prevents GBK codec crash when outputting emoji (e.g. 🏷️ U+1F3F7) in JSON.
if sys.stdout and hasattr(sys.stdout, 'buffer') and sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer') and sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration for external tool
EXTERNAL_TOOL_PATH = r"I:\DeepSeek_text"
# Phase 2: Industrial Discovery Cache (Portable side-car)
CACHE_FILENAME = ".memory_retriever_cache"

def _safe_print_json(obj, indent=2):
    """Unicode-safe JSON output that bypasses Windows codepage limitations."""
    try:
        text = json.dumps(obj, ensure_ascii=False, indent=indent)
    except (UnicodeEncodeError, UnicodeDecodeError):
        text = json.dumps(obj, ensure_ascii=True, indent=indent)
    # Write directly to binary buffer to avoid any encoding layer issues
    sys.stdout.buffer.write(text.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')
    sys.stdout.buffer.flush()

def local_index_scan(memory_root, query):
    """
    Level 1: Quick scan of index files.
    Returns a list of matches from *_index.md files.
    """
    root_path = Path(memory_root)
    results = []
    
    if not root_path.exists():
        return []

    # Find all index files
    index_files = list(root_path.glob("*_index.md"))
    
    keywords = query.lower().split()
    
    for idx_file in index_files:
        try:
            with open(idx_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines):
                if "|" not in line: continue # Skip non-table lines
                
                # Simple keyword matching
                line_lower = line.lower()
                if any(k in line_lower for k in keywords):
                    results.append({
                        "source": "Level 1 (Index Scan)",
                        "file_path": str(idx_file),
                        "content_snippet": line.strip(),
                        "score": 1.0 # High confidence since it's an index hit
                    })
        except Exception:
            continue
            
    return results

def update_vitality_metrics(file_path_str, snippet=None):
    """
    Intelligently updates the VITALITY field in the specified file using YAML parsing.
    Maintains future extensibility by not corrupting parallel YAML attributes.
    """
    file_path = Path(file_path_str)
    if not file_path.exists():
        return

    try:
        import yaml
        content = file_path.read_text(encoding="utf-8")
        
        # Regex to find all YAML blocks
        pattern = re.compile(r'```yaml\n(.*?)\n```', re.DOTALL)
        matches = list(pattern.finditer(content))
        
        if not matches:
            return

        target_match = None
        
        if snippet:
            # Find the best chunk
            snippet_clean = re.sub(r'\s+', ' ', snippet).strip()
            idx = content.find(snippet[:50])
            if idx != -1:
                for m in reversed(matches):
                    if m.start() < idx:
                        target_match = m
                        break
        
        if not target_match and matches:
            target_match = matches[0]

        if target_match:
            yaml_str = target_match.group(1)
            try:
                # Load YAML safely
                parsed_yaml = yaml.safe_load(yaml_str) or {}
                
                if isinstance(parsed_yaml, dict):
                    # Intelligent creation / update
                    if 'vitality' not in parsed_yaml or not isinstance(parsed_yaml['vitality'], dict):
                        parsed_yaml['vitality'] = {'usage': 0, 'last_ref': datetime.datetime.now().strftime("%Y-%m-%d")}
                    
                    # Update usage and last_ref
                    current_usage = parsed_yaml['vitality'].get('usage', 0)
                    try:
                        current_usage = int(current_usage)
                    except:
                        current_usage = 0
                        
                    parsed_yaml['vitality']['usage'] = current_usage + 1
                    parsed_yaml['vitality']['last_ref'] = datetime.datetime.now().strftime("%Y-%m-%d")
                    
                    # Dump YAML back cleanly (prevent alphabetically sorting keys if possible, but safe_dump sorts by default. We just let it sort or set sort_keys=False)
                    new_yaml_str = yaml.dump(parsed_yaml, sort_keys=False, allow_unicode=True, default_flow_style=None)
                    
                    # Some formatting adjustments to keep it looking like inline dict if the user wrote it that way
                    # PyYAML might format vitality: {usage: 1, last_ref: '...'} or multi-line. Both are valid.
                    
                    # Reconstruct block
                    new_block = f"```yaml\n{new_yaml_str.strip()}\n```"
                    
                    new_content = (
                        content[:target_match.start()] + 
                        new_block + 
                        content[target_match.end():]
                    )
                    
                    # Atomic write
                    temp_path = file_path.with_suffix('.tmp')
                    temp_path.write_text(new_content, encoding="utf-8")
                    temp_path.replace(file_path)
            except yaml.YAMLError:
                pass # Silently fail if yaml is corrupted
                
    except Exception as e:
        pass

def main():
    """
    SOTA Smart Argument Resolver: Handles raw strings, mangled JSON, and 3-Step Protocol bypass.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("args", nargs="*", help="JSON params or raw query string")
    cli_args = parser.parse_args()

    # 1. Join all arguments to handle shell splitting
    raw_input = " ".join(cli_args.args).strip()
    
    if not raw_input:
        # Check stdin for pipe support
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read().strip()

    # [SOTA Fix] Strip surrounding quotes (CMD/Shell artifact handling)
    # This ensures '{"a":1}' is parsed as JSON object, not string query.
    if len(raw_input) >= 2 and raw_input[0] in ["'", '"'] and raw_input[-1] == raw_input[0]:
        # Check if it looks like a JSON object inside quotes
        inner = raw_input[1:-1].strip()
        if inner.startswith('{') or inner.startswith('['):
            raw_input = inner
    
    if not raw_input:
        _safe_print_json({"status": "error", "message": "No input provided"})
        return

    params = {}
    
    # 2. Smart Parsing Logic
    if raw_input.startswith('{') or raw_input.startswith('['):
        try:
            # Standard JSON
            params = json.loads(raw_input)
        except json.JSONDecodeError:
            # Attempt SOTA repair for common shell quotation stripping
            try:
                # Case: {\"query\": \"val\"} or escaped quotes
                cleaned = raw_input.replace('\\"', '"').replace('\\\\', '\\')
                params = json.loads(cleaned)
            except:
                # If it looks like JSON but fails, and is not obviously a raw string
                # We treat as raw if query key is missing or logic is too mangled
                params = {"query": raw_input}
    else:
        # Case: Raw string or key:val pairs without braces
        # We treat as a direct query for best UX
        params = {"query": raw_input}

    # Extract parameters with defaults
    query = params.get("query", "")
    target_dirs = params.get("target_dirs", [])
    limit = params.get("limit", 5)
    target_level = params.get("level", 0) # 0=normal, 3=forced Deep RAG
    manual_root = params.get("root") # Optional manual root override

    if not query:
        _safe_print_json({"status": "error", "message": "Missing 'query'"})
        return
        
    # --- Intelligent Domain Discovery (SOTA 4.2.0) ---
    def find_workspace_root():
        """Attempts to find the workspace root with multi-layer fallback caching."""
        # 1. Check Environmental Override (Highest Priority)
        env_root = os.environ.get("MEMORY_WORKSPACE_ROOT")
        if env_root and Path(env_root).exists():
            return Path(env_root)

        script_dir = Path(__file__).resolve().parent
        cache_file = script_dir / CACHE_FILENAME

        # 2. Check current working directory
        cwd = Path.cwd()
        for p in [cwd] + list(cwd.parents):
            if (p / ".记忆").is_dir() or (p / ".项目进展").is_dir():
                # Update cache on success
                try: cache_file.write_text(str(p.resolve()), encoding="utf-8")
                except: pass
                return p
        
        # 3. Check script directory ancestors (traditional logic fallback)
        for p in [script_dir] + list(script_dir.parents):
            if (p / ".记忆").is_dir() or (p / ".项目进展").is_dir():
                try: cache_file.write_text(str(p.resolve()), encoding="utf-8")
                except: pass
                return p
        
        # 4. Phase 2: Recovery from Portable Cache (Side-car)
        if cache_file.exists():
            try:
                cached_path = Path(cache_file.read_text(encoding="utf-8").strip())
                if cached_path.exists() and ((cached_path / ".记忆").is_dir() or (cached_path / ".项目进展").is_dir()):
                    return cached_path
            except: pass

        # 5. Default back to the hardcoded 3-level parent if nothing found
        return script_dir.parent.parent.parent

    # Resolve workspace root candidate
    workspace_root = Path(manual_root) if manual_root else find_workspace_root()
    workspace_root = workspace_root.resolve()
    
    potential_domains = []
    if target_dirs:
        # Resolve any relative paths against the workspace root
        for d in target_dirs:
            p = Path(d)
            if not p.is_absolute():
                p = workspace_root / d
            potential_domains.append(p.resolve())
    else:
        # Default smart discovery: Check known domains in workspace root
        # Scanning for hidden directories that might be memory domains
        for domain in workspace_root.iterdir():
            if domain.is_dir() and domain.name.startswith(".") and domain.name not in [".git", ".venv", ".gemini", ".idea", ".vscode"]:
                potential_domains.append(domain)
        
        # Priority sort: ensure .记忆 and .项目进展 processed if present
        priority = {".记忆": 0, ".项目进展": 1}
        potential_domains.sort(key=lambda x: priority.get(x.name, 999))

    if not potential_domains:
        _safe_print_json({"status": "error", "message": "No memory domains discovered in workspace."})
        return

    final_results = []
    scan_errors = []
    scanned_domains = []
    
    import subprocess
    
    for domain_path in potential_domains:
        if not domain_path.exists():
            continue
            
        memory_root = str(domain_path)
        scanned_domains.append(memory_root)
        
        if len(final_results) >= limit:
            break
            
        # --- Level 1: Index Scan (Bypassable) ---
        if target_level < 3:
            try:
                index_hits = local_index_scan(memory_root, query)
                if index_hits:
                    needed = limit - len(final_results)
                    hits_to_add = index_hits[:needed]
                    final_results.extend(hits_to_add)
                    
                    for res in hits_to_add:
                        if 'file_path' in res:
                            update_vitality_metrics(res['file_path'], res.get('content_snippet'))
                
                # [SOTA Fix] Early exit conditions:
                # 1. Level 1 is explicitly requested (Strict Bypass)
                # 2. Level 0 (Default) found enough results in Index Scan
                # This prevents the ~15s cold-start penalty of the RAG backend.
                if target_level == 1:
                    continue # Skip Level 2/3 for this domain
                if target_level == 0 and len(final_results) >= limit:
                    continue # Sufficient results found, skip slow RAG
                    
            except Exception as e:
                scan_errors.append(f"Level 1 error in {domain_path.name}: {str(e)}")
                
        remaining_limit = limit - len(final_results)
        if remaining_limit <= 0:
            continue
            
        # --- Level 2 & 3: External RAG ---
        try:
            # SOTA: UV Run Isolation with Absolute Paths
            rag_tool_script = os.path.join(EXTERNAL_TOOL_PATH, "scripts", "RAG_FAISS_tool.py")
            
            cmd = [
                "uv", "run", 
                "--project", EXTERNAL_TOOL_PATH, 
                "python", rag_tool_script,
                "--json",
                memory_root,
                query
            ]
            
            # [SOTA] Force UTF-8 encoding in subprocess via environment injection.
            # This prevents GBK codec errors when the backend outputs emoji/CJK.
            child_env = os.environ.copy()
            child_env["PYTHONIOENCODING"] = "utf-8"
            child_env["PYTHONUTF8"] = "1"  # PEP 686: Python 3.15+ UTF-8 mode
            
            result = subprocess.run(cmd, capture_output=True, text=False, timeout=120, env=child_env)
            
            def robust_decode(data):
                if not data: return ""
                for enc in ["utf-8", "gbk", "cp936"]:
                    try: return data.decode(enc)
                    except UnicodeDecodeError: continue
                return data.decode("utf-8", errors="replace")

            stdout_str = robust_decode(result.stdout)
            stderr_str = robust_decode(result.stderr)
            
            if result.returncode != 0:
                # Capture specific error message from JSON if possible
                try:
                    err_json = json.loads(stdout_str[stdout_str.find('{'):stdout_str.rfind('}')+1])
                    scan_errors.append(f"Level 2 error in {domain_path.name}: {err_json.get('error', 'Unknown backend error')}")
                except:
                    scan_errors.append(f"Level 2 process error in {domain_path.name} (Code {result.returncode})")
                continue
                
            json_start = stdout_str.find('{')
            json_end = stdout_str.rfind('}')
            if json_start != -1 and json_end != -1:
                clean_json = stdout_str[json_start:json_end+1]
                rag_data = json.loads(clean_json)
                
                if "error" in rag_data:
                    scan_errors.append(f"Backend error in {domain_path.name}: {rag_data['error']}")
                    continue

                rag_results = rag_data.get("semantic_results", [])
                mapped_results = []
                for res in rag_results:
                    mapped_results.append({
                        "source": f"Level 2 (Semantic) - {domain_path.name}",
                        "file_path": res.get("path"),
                        "content_snippet": res.get("text", "")[:300],
                        "score": res.get("score", 0.0)
                    })
                    
                hits_to_add = mapped_results[:remaining_limit]
                final_results.extend(hits_to_add)
                for res in hits_to_add:
                    if res.get('file_path'):
                        update_vitality_metrics(res['file_path'], res.get('content_snippet'))
            else:
                scan_errors.append(f"No JSON output from backend for {domain_path.name}")
                            
        except subprocess.TimeoutExpired:
            scan_errors.append(f"Timeout while scanning {domain_path.name}")
        except Exception as e:
            scan_errors.append(f"Level 2/3 exception in {domain_path.name}: {str(e)}")

    if final_results:
        # Sort combined results by score (descending)
        final_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        _safe_print_json({
            "status": "success",
            "query": query,
            "data": final_results[:limit],
            "scanned_domains": [str(p) for p in scanned_domains],
            "errors": scan_errors if scan_errors else None
        })
    else:
        if scan_errors:
            # Differentiate between technical failure and "no results"
            _safe_print_json({
                "status": "error", 
                "message": "Retrieval failed due to technical errors.",
                "scanned_domains": [str(p) for p in scanned_domains],
                "errors": scan_errors
            })
        else:
            _safe_print_json({
                "status": "error", 
                "message": "No matching records found in documented domains.",
                "scanned_domains": [str(p) for p in scanned_domains]
            })


if __name__ == "__main__":
    main()

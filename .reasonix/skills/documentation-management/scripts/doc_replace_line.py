# -*- coding: utf-8 -*-
"""
scripts/doc_replace_line.py - 文档按行/按内容安全替换
用途: 当 StrReplace 因文件内含 Unicode（如弯引号 ""）、编码或不可见字符导致匹配失败时，
      用本脚本做按行替换或 UTF-8 安全的内容替换，避免在对话里写临时 Python 片段。
使用:
  python scripts/doc_replace_line.py --file .项目进展/当前_项目进展.md --line 24 --new "| \`tests/04_hil/...\` | ..."
  python scripts/doc_replace_line.py --file .项目进展/当前_项目进展.md --old "某段旧内容" --new "新内容"
依赖: 无，仅标准库。UTF-8 读写。
"""
import argparse
import sys


def replace_by_line(path: str, line_1based: int, new_content: str) -> bool:
    """将第 line_1based 行（从 1 计）替换为 new_content，不自动加换行。"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if line_1based < 1 or line_1based > len(lines):
        print(f"[doc_replace_line] line {line_1based} out of range [1, {len(lines)}]", file=sys.stderr)
        return False
    lines[line_1based - 1] = new_content if new_content.endswith("\n") else new_content + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def replace_by_content(path: str, old: str, new: str, first_only: bool = True) -> bool:
    """将文件中第一次出现的 old 替换为 new（UTF-8 安全）。"""
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    if old not in s:
        print("[doc_replace_line] old string not found", file=sys.stderr)
        return False
    s = s.replace(old, new, 1 if first_only else -1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    return True


def main():
    ap = argparse.ArgumentParser(description="文档按行或按内容安全替换 (UTF-8)")
    ap.add_argument("--file", "-f", required=True, help="目标文件路径")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--line", "-l", type=int, help="要替换的行号 (从 1 开始)")
    g.add_argument("--old", "-o", help="要替换的旧内容 (首次出现)")
    ap.add_argument("--new", "-n", required=True, help="新内容")
    ap.add_argument("--all", action="store_true", help="与 --old 联用：替换所有出现（默认只替换第一次）")
    args = ap.parse_args()

    if args.line is not None:
        ok = replace_by_line(args.file, args.line, args.new)
    else:
        ok = replace_by_content(args.file, args.old, args.new, first_only=not args.all)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

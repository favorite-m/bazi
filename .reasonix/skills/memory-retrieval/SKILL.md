---
name: memory-retrieval
description: 当需要跨会话恢复用户命案分析记录、搜索历史命理知识结晶（如格局经验、神煞用法、断事技巧）、回顾项目进展、或快速理解八字命理分析项目中已有知识库全貌时使用。也用于初次对话时恢复对项目的理解，或在方案整理前检索相关命理知识。
---

# 八字命理语义检索技能 (Bazi Semantic Retrieval Skill)

## 描述
此技能通过调用 `memory_retriever.py` 脚本实现基于向量的语义检索能力，能够跨越 `.记忆`（命理知识库）和 `.项目进展`（项目演进记录）目录，根据自然语言查询找到最相关的文档片段。它是 Agent 获取"长期命理知识记忆"和"项目上下文感知"的核心手段。

## 适用场景
- **命理知识盲区**: 不确定某种格局（如"杀印相生"）的断事要点、某个神煞的用法、或某个流年组合的断法时。
- **客户身份确认**（新对话时）: 搜索 `/客户档案/` 下是否有匹配的客户档案，避免重复建档。
- **查阅历史分析**: 需要回顾之前某位用户的命盘分析记录、喜用神校正结果、或前事校验反馈。
- **按需加载分析文件**: 不一次性读取整个客户文件夹，通过脚本查询精确定位需要的文件。
- **避免重复研究**: 在开始新的命理体系研究前，确认是否已有相关的知识结晶，避免重复劳动。
- **上下文恢复**: 在长对话中断后，快速恢复对项目当前状态和已有命理知识库的理解。

## 核心检索策略 (Retrieval Strategy)
为了平衡速度与精度，本技能遵循严格的 **三级检索协议 (3-Step Protocol)**：

根据需要了解的信息是要了解项目进展相关（`.项目进展`）还是命理知识相关（`.记忆`）的目录，扫描对应的文件夹：

1. **Level 1: 快速索引扫描 (Index Scan)**
   - 优先读取有 index 的目录，例如 `当前_XX_index.md` 和 `核心_XX_index.md`。XX代表是项目进展或者是记忆相关的目录
   - 这通常能覆盖 80% 的高频上下文需求，且消耗 Token 最少。

2. **Level 2: 索引级 RAG (Index RAG)**
   - 如果 Level 1 的信息不足，调用 `memory_retriever.py` 对 `历史_XX_index.md` 进行向量检索。
   - 目的是快速定位到具体的归档文件路径，而不必扫描全库。

3. **Level 3: 全局深度 RAG (Full Deep RAG)**
   - 如果仍未找到答案，调用 `memory_retriever.py` 对 **所有 Markdown 文档** (包括 `存档/` 下的冷数据) 进行全量向量检索。
   - 这是最终的兜底手段，用于挖掘深层细节。

## 核心能力

### 语义检索 (Semantic Search)
- **指令**: `semantic-retrieval` (隐含调用)
- **底层脚本**: `memory_retriever.py` 脚本

## 脚本使用说明

> **⚠️ 执行前置条件**：由于脚本在项目中的实际路径可能因环境而异，Agent **必须** 先通过搜索定位 `memory_retriever.py` 的绝对路径，然后再构造命令执行。**严禁**直接使用相对路径（如 `memory-retrieval/scripts/memory_retriever.py`）发起首次调用。

### 执行流程（必须严格遵守）

1. **第一步：定位脚本的真实路径**  
   - **Windows (PowerShell)**:  
     `Get-ChildItem -Recurse -Path . -Filter "memory_retriever.py" | Select-Object -First 1 -ExpandProperty FullName`  
   - **Linux / macOS**:  
     `find . -name "memory_retriever.py" -print -quit`  
   - 将输出结果（第一个命中的绝对路径）保存为变量 `$SCRIPT_PATH`，供后续命令使用。

2. **第二步：根据需求选择参数组合并执行**  
   - 将以下任一命令中的 `$SCRIPT_PATH` 替换为上一步获得的真实路径，然后执行。

### 常用命令参数组合

| 场景 | 命令示例 |
|------|----------|
| 1. **命理知识查询** (推荐) | `python "$SCRIPT_PATH" --query "杀印相生格局 断事要点" --target-dir .记忆` |
| 2. **多目录联合查询** | `python "$SCRIPT_PATH" --query "用户张三 命盘分析 喜用神" --target-dir .记忆 --target-dir .项目进展` |
| 3. **客户身份确认** | `python "$SCRIPT_PATH" --query "癸水 财多身弱 1997" --target-dir /客户档案` |
| 4. **读取客户基础信息** | `python "$SCRIPT_PATH" --query "xxx 基础信息 日主 喜用神" --target-dir /客户档案/xxx` |
| 5. **强制深度检索** | `python "$SCRIPT_PATH" --query "大运流年 断法技巧" --level 3` |
| 6. **指定工作空间根目录** | `python "$SCRIPT_PATH" --query "紫微斗数 星曜组合" --root "C:/path/to/workspace"` |

### 完整执行示例（Windows PowerShell）

```powershell
# 第一步：定位脚本路径
$scriptPath = Get-ChildItem -Recurse -Path . -Filter "memory_retriever.py" | Select-Object -First 1 -ExpandProperty FullName

# 查询命理格局相关记忆
python "$scriptPath" --query "食神生财 格局 事业分析" --target-dir .记忆

# 查询用户命盘分析记录
python "$scriptPath" --query "用户李四 命盘 分析记录" --target-dir .记忆 --target-dir .项目进展

# 新对话时：确认客户是否存在（只读总目录）
python "$scriptPath" --query "xxx 客户 档案" --target-dir /客户档案

# 按需读取客户基础信息（不加载全量文件）
python "$scriptPath" --query "xxx 日主 喜用神 四柱" --target-dir /客户档案/xxx
```

### 脚本执行遇到问题
若执行时遇到 `[Errno 2] No such file or directory` 错误，Agent **必须** 立即执行以下补救措施，**无需** 询问用户：
1. **检索**: 使用 `glob` 或 `find` 工具搜索文件名 `memory_retriever.py`。
   - *Windows*: `Get-ChildItem -Recurse -Filter "memory_retriever.py" | Select-Object -ExpandProperty FullName`
   - *Linux/Mac*: `find . -name "memory_retriever.py"`
2. **重试**: 第一个命中的就是真实地址，获取真实路径后，使用新路径再次尝试执行命令。

### 参数传递最佳实践
- 优先使用 **标准参数模式** (`--query "..."`) 而非 JSON 模式，以减少 Shell 转义错误。
- 在 Windows PowerShell 中，确保参数值中的双引号被正确转义，或使用单引号包裹参数值（如果 Shell 支持）。

## 返回格式 (Return Format)

`memory_retriever.py` 脚本检索结果统一以 **UTF-8 JSON** 格式通过标准输出 (stdout) 返回：

```json
{
  "status": "success",
  "query": "杀印相生格局 断事要点",
  "data": [
    {
      "source": "Level 1 (Index Scan)",
      "file_path": "C:\\project\\.记忆\\核心_记忆.md",
      "content_snippet": "## [PATTERN_SHAYIN_GRID] 杀印相生格局断事要点\n...",
      "score": 1.0
    }
  ],
  "scanned_domains": ["C:\\project\\.记忆"],
  "errors": null
}
```

- **status**: `success` 表示成功，`error` 表示发生技术故障（如子进程超时）。
- **data**: 匹配到的片段列表。
  - `source`: 来源标识（Level 1 索引或 Level 2/3 语义）。
  - `score`: 置信度。L1 命中默认为 1.0；语义匹配返回相似度得分。
  - `content_snippet`: 检索到的原始文本块。
- **errors**: 包含可能发生的非致命性警告或错误。

## 注意事项
1. **JSON 格式**: 参数必须是严格的 JSON 格式。在 Windows 下建议使用 `\"` 转义双引号。
2. **存活度权重 (Vitality Ranking)**: 本系统使用 `vitality: { usage: X, last_ref: YYYY-MM-DD }` 贯穿所有记忆。在查阅返回的片段时，请**务必关注其 YAML 头部的 usage 字段**。如果有冲突的记忆，以 `usage` 次数高且不为 `OBSOLETE` 的记录为最终权威依据。
3. **解析架构**: 检索到的数据块会原样保留 `.记忆` 和 `.项目进展` 中定义的 Markdown YAML 代码块。这能帮你免除幻觉，准确定位知识的修改点。
4. **调试旁路**: 如需验证 RAG 全局召回能力，可在参数中指定 `--level 3`。

---
name: git-management
description: 当需要 Git 版本控制规范、分支管理及提交信息标准时候使用。
---

# Git Management

## 描述
规范 Agent 的 Git 操作行为，确保提交历史清晰、可追溯，并有效处理合并冲突。

## 适用场景
*   提交代码 (Commit) 时。
*   创建新功能分支 (Branch) 时。
*   解决代码冲突 (Merge Conflicts) 时。
*   查看变更 (Diff/Status) 时。

## 指令 (Instructions)

### 1. 提交前检查 (Pre-commit)
在执行 `git commit` 之前，必须：
1.  **`git status`**: 确认哪些文件被修改了。
2.  **`git diff`**: 仔细审查每一行改动，确保没有意外的修改（如调试打印、临时注释）。
3.  **Run Tests**: 确保改动没有破坏现有功能。

### 2. 提交信息规范 (Commit Messages)
采用 **Conventional Commits** 格式：
`type(scope): description`

*   **Types**:
    *   `feat`: 新功能
    *   `fix`: 修复 Bug
    *   `docs`: 文档变更
    *   `style`: 格式调整 (不影响逻辑)
    *   `refactor`: 重构 (既不修 bug 也不加功能)
    *   `test`: 增加或修改测试
    *   `chore`: 构建过程或辅助工具的变动
*   **Example**: `feat(auth): 增加 JWT 登录验证功能`

### 3. 分支策略 (Branching)
*   不要直接在 `main` 或 `master` 分支工作（除非是极小的文档修复）。
*   **命名规范**:
    *   功能: `feat/功能名称` (e.g., `feat/login-page`)
    *   修复: `fix/bug名称` (e.g., `fix/memory-leak`)

### 4. 冲突解决 (Conflict Resolution)
1.  识别冲突文件 (`<<<<<<<`, `=======`, `>>>>>>>`)。
2.  理解双方意图：Incoming Change (新代码) vs Current Change (旧代码)。
3.  手动合并逻辑，而不是简单选择一方。
4.  运行测试验证合并后的代码。

### 5. 安全提醒
*   **严禁提交 Secrets**: 检查是否有 API Key、密码、`.env` 文件被加入暂存区。

# Visual AI Logic Refactor (Playwright + Claude Code Bridge)

> **将网页视觉审查与 Claude Code 深度结合的自动化逻辑重构工具。** 
> 无需手动查找组件和源码位置，直接在运行中的界面上通过 `Shift + 点击` 选中元素、添加批注，即可驱动 AI 自动完成代码逻辑的批量重构与修改！

---

## 🌟 核心特性

*   **视觉得到即所得 (Visual Inspection)**：按住 `Shift` 键即可高亮选中页面上的任意 DOM 元素，自动捕获标签名、类名、绑定的事件（如 `@click`）、DOM 祖先链及周围上下文。
*   **批量交互批注看板 (Batch Annotation Panel)**：内置优雅的 Dark 风格侧边看板与交互弹窗，支持连续添加多个修改需求（如表单校验绕过、接口模拟、逻辑修改等）。
*   **全自动 Claude Code 流水线**：一键触发后，脚本会按顺序生成任务上下文 (`task_context.md`)，并自动调用本地的 `claude` CLI（带 `--dangerously-skip-permissions` 权限）对项目代码进行深度读写和重构。
*   **实时终端状态流 (Live Status Stream)**：集成动态加载动画与耗时统计，实时反馈每一个任务的执行进度与后台输出日志。

---

## ⚙️ 运行流程

```text
[浏览器页面 (localhost:8888)] 
       │ (按住 Shift + 点击元素)
       ▼
[前端注入脚本收集批注] ──► [导出并触发 Console 通信]
                                  │
                                  ▼
[Python 异步主控进程捕获数据]
       │
       ├─► 依次写入 task_context.md
       └─► 循环调用 Claude Code 命令行进行自主重构 ──► [自动修改本地代码文件]

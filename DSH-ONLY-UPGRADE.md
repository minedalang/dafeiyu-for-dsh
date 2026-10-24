# DSH-only 升级说明（v8.2 工作分支）

这版基于此前 v8.2 DSH 控制权代码整理；不是 Windows 安装包，Windows/DSH 联调仍要本机验收。

## 删除/停用的 Agent 功能

- 删除 `pet/desktop_agent.py`（OpenClaw Gateway）、`pet/agent_context.py`（旧 `/agent` 摘要缓存）、`pet/windows_agent_mcp.py`（OpenClaw Windows MCP）及相应专属测试。
- 完整/经典聊天窗与快捷气泡不再识别或调用 OpenClaw；输入 `/agent` 会提示去 DSH，不会执行 Agent 任务。
- 删除设置页的 OpenClaw Gateway、Token、模型、上下文摘要、工具白名单和测试网关选项。
- Agent 联动菜单与运行中的监视器仅保留 DSH，删除 Claude Code hooks、Cursor、OpenCode、自定义 Agent 的代码路径，以及 Hermes 插件目录。
- 新旧配置加载时将旧 `agent_link.claude/cursor/opencode/custom_agents` 字段丢弃，写盘时移除 `desktop_agent`。**原始用户配置与系统密钥串不会被直接清空**；必要时请自行备份后清理旧凭据。

## 保留

- DSH 双向桥接：`dsh-pet-bridge`、`dsh-pet-actions`，`pet_action` 和 `pet_animations`。
- DSH 理解正在执行的任务后自主决定台词和动画，不需要桌宠再调用第二个模型作任务反应判断。
- 大肥鱼本地 AI 自主生活、生命系统、可选自主识屏、普通聊天与角色会话，包括可使用 Claude **模型 API** 的能力。
- DSH 工作控制权与自主行为的冲突协调；工具动作有限时长、动作素材精确匹配与接收回执。

## Windows 操作建议

1. **备份项目目录和 `%APPDATA%` 下桌宠相关数据**；当前已装桥接的 DSH Profile 也保留备份。
2. 解压增量补丁到项目根目录，按路径合并/删除，不要把完整源码覆盖到你已经继续修改的版本。
3. 如需彻底移出旧版源码文件，执行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Remove-Legacy-Agent-Files.ps1`（会先备份到项目目录外）。然后源码运行 `2-Run-Windows.bat`，确认大肥鱼正常出现、设置中找不到 OpenClaw 配置、Agent 联动菜单仅有 DSH。
4. DSH 桥接已有且可用时可先继续使用；若 DSH 里还只看见旧 `pet_action` 参数，再从桌宠的 DSH 联动入口刷新插件，重启 DSH。
5. 在 DSH 中先试 `pet_animations`，再试 `pet_action(mood="happy", speech="我看到啦！")`；必要时运行 `scripts/Test-PetAction.ps1` 做本机端到端诊断。

**卸载边界：** 本补丁不会卸载你电脑上独立安装的 OpenClaw、Claude Code 或 Cursor，也不会自动删除你 `.claude/settings.json` 中旧版注入的 hooks。它只从大肥鱼**源码与交互入口**移除对应集成。需要清理旧 hooks 时请人工确认仅删除与 `claude_event_hook` 关联的条目，不要清空其他工具的配置。

## 测试与限制

- Python 静态语法检查已通过；DSH 插件需要你的 DSH Profile 实际加载测试。
- Python 现有测试主要可在不安装 Qt 的环境中运行；旧版中已存在午睡时长、旧视觉测试桩两类失败，未把它们冒充为新增回归。
- 本补丁**不**给大肥鱼普通聊天窗新增 DSH 对话路由；电脑任务始终在 DSH 界面发起。

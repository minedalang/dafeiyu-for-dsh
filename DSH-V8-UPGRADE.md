# 大肥鱼 v8 — DSH 双向联动（增量源码升级）

本补丁以此前提供的 **v7 完整源码包** 为基线；你本地如果已继续修改源码，请先做备份、查看差异再逐文件合并，**不要把整个包直接覆盖较新的独立项目**。

## 本次新增

1. **DSH → 大肥鱼 `pet_action` 工具**：DSH Agent 可用 `pet_action` 选择 `search / watch / think / happy / work / idle` 六种情绪状态和可选的 90 字以内台词。桌宠只播放本地素材库中实际存在的匹配动画，没有匹配动画时只显示气泡，不下载或生成素材。
2. **B 站工具阶段联动**：现有 DSH 事件桥会检测模型可见的 B 站工具调用，输出 `dsh/activity`，只存 `site=bilibili` 和 `stage=search / browse / play / summarize`。本地桌宠在工作中显示对应的观察/思考/开心反馈。普通浏览器打开 B 站只记为浏览，不代表视频真正开始播放。
3. **减少打断**：DSH 场景活动 25 秒内不会频繁重复触发；跨阶段最短 3 秒；模型显式动作最短 2 秒；仍采用原有 `request_link_anim()` 的一次性动作衔接规则，隐藏桌宠不主动显示；保留原 AI 自主行为模块。
4. **隐私与约束**：自动 B 站检测不把 URL、页面正文、视频标题、命令参数写入事件日志；`pet_action` 会在本地桥文件短暂记录你主动填写的台词。此工具不能读写文件、不能执行系统命令、也不能控制真实鼠标键盘。队列提交成功并不等于桌宠已经呈现成功。

## 覆盖的文件

- `pet/agent_link.py` — 接收两类新事件，转已有动画/气泡接口。
- `pet/dsh_pet_feedback.py` — 纯逻辑白名单、素材匹配及输入检查。
- `integrations/dsh-pet-bridge/index.js` — 隐私安全的 B 站阶段侦测和事件写入。
- `integrations/dsh-pet-bridge/actions.js` — 新的 DSH 模型可调用 `pet_action` 工具。
- `integrations/dsh-pet-bridge/package.json`, `cordis.patch.yml` — 工具注册与打包声明。
- `tests/test_dsh_pet_feedback_v8.py`, `tests/dsh_v8_node_smoke.mjs` — 针对性测试。

## Windows 安装 / 升级流程

1. **先退出大肥鱼、备份你的源码与应用数据目录**，再解压补丁到项目根目录，按文件路径覆盖。若你已有 v7 之后的个人改动，先手动合并这些文件。
2. 运行大肥鱼（例如 `2-Run-Windows.bat`），进入 **Agent 联动**，若原来已经启用 DSH，先关闭该联动，再打开并同意重新安装桥接插件。原项目的安装器会将本地新版插件刷新到已经存在的 DSH Profile。避免只重启 DSH 却仍链接到旧目录。
3. 完全退出并重启 DSH（你实际在用的 Web 或 Desktop Profile）；启动大肥鱼并保持 DSH 联动开启。
4. 在 DSH 中输入：`请调用 pet_action 工具，mood=happy，speech=找到视频啦！`。大肥鱼显示气泡；如果角色素材有开心相关动画，播放相应动画。**工具返回 queued，只代表写入了事件队列，不是终端播放确认。**
5. 再在 DSH 里用 Agent 可调用的 B 站搜索或浏览工具搜索/打开 B 站视频。模型执行对应工具调用时，桌宠应出现观察/搜索等反馈。如果独立的 B 站插件在后台运行但不向 DSH `session/event` 汇报工具调用，则此补丁 **不会**知道它看了什么；需为那个 B 站插件另外增加事件发射点。

## 手动验证与排错

Windows 本地事件日志通常位于 `%APPDATA%\dsh-pet-bridge\dsh-*.jsonl`。只检查是否出现类似下面两类**枚举事件**，无需复制日志里的其他敏感字段：

```json
{"event":"dsh/activity","site":"bilibili","stage":"search"}
{"event":"pet/action","action":"express","mood":"happy","speech":"找到视频啦！"}
```

- DSH 里没有 `pet_action` 工具：旧版插件仍被 Profile 引用，检查桥接安装及 `cordis.patch.yml` 的 `dsh-pet-actions` 节点，重启 Profile。
- DSH 提示已入队而桌宠不动：确认大肥鱼正在运行、DSH 联动已开、桌宠可见；检查有无匹配动画（没有动画时只显示气泡）；并注意事件时效和限频。
- 只显示 `working` 而没有 B 站阶段：可能是后台插件内部工作、模型没调用暴露的工具，或工具参数中未出现 B 站网站地址。不会为了识别视频而突破匿名化保存原始浏览器内容。
- **注意：这份是旧 v8 升级历史记录**。当前 DSH-only 版已经移除 OpenClaw，请以 `DSH-ONLY-UPGRADE.md` 为准。

## 回归测试与验收边界

Linux 上运行 `PYTHONPATH=. pytest -q tests`：**77 通过、2 失败、5 subtests 通过**。其中 2 项失败在没有任何 v8 改动的 v7 原始源码上也可复现（午睡持续时间的旧断言、`_complete_json` 模拟接口测试）。v8 Python 专项与相关测试 15 项通过；Node 工具、B 站阶段写盘测试通过。

**尚未验证**：用户 Windows 机器上真实 DSH Profile 的插件装载、`pet_action` 实际模型调用，以及 Qt 桌宠的真实动作呈现。这些需要在安装后按上面的步骤验收。不要把测试桩通过当成生产环境功能已验证。

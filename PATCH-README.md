# v8.2 DSH-only 增量补丁（适用于 v8.1 源码及其派生项目）

**先退出大肥鱼，备份整个项目和用户数据目录。**

1. 将补丁解压到项目根目录，检查差异并按原相对路径合并。
2. PowerShell 在项目根目录运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Remove-Legacy-Agent-Files.ps1 -DryRun` 预览需要移走的旧源码。
3. 确认后不加 `-DryRun` 重新运行，脚本把旧 OpenClaw／其他 Agent 文件备份到**项目目录旁边**，不删系统里的独立软件。
4. 运行 `2-Run-Windows.bat`，确认 Agent 联动菜单仅有 DSH；如果 DSH 里 `pet_animations` 不出现，先更新 DSH 桥接并重启 Profile。
5. 详见 `DSH-ONLY-UPGRADE.md`。

**注意**：这份压缩包不是 EXE 安装程序。它不负责卸载已经装在电脑上的 OpenClaw、Claude Code、Cursor、OpenCode，也不自动清除系统凭据或其他程序自己的配置文件。

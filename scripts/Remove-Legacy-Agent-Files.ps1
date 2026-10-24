# Remove obsolete agent source files from a pre-v8.2 project checkout.
# Does NOT uninstall OpenClaw, Claude Code, Cursor, etc. or touch user config.
# Moves known legacy files to a sibling backup folder instead of deleting permanently.
param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not ((Test-Path (Join-Path $project 'pet\config.py')) -and
          (Test-Path (Join-Path $project 'integrations\dsh-pet-bridge\index.js')))) {
    throw '请在大肥鱼项目根目录里的 scripts 中运行本脚本。'
}
$targets = @(
  'pet\desktop_agent.py',
  'pet\agent_context.py',
  'pet\windows_agent_mcp.py',
  'integrations\hermes-pet-bridge',
  'tests\test_desktop_agent_bridge.py',
  'tests\test_agent_context_summary.py',
  'tests\test_agent_integration_v4.py',
  'AGENT-CONTEXT-SUMMARY-V7.md',
  'CHAT-API-SEPARATION-FIX.md',
  'docs\OPENCLAW-DESKTOP-AGENT.md',
  'docs\AGENT-SETTINGS-V2.md',
  'docs\AGENT-CHAT-SETTINGS-V4.md'
)
$present = @($targets | Where-Object { Test-Path -LiteralPath (Join-Path $project $_) })
if ($present.Count -eq 0) {
    Write-Host '没有发现需要移出的旧 Agent 文件。'
    return
}
$folder = Split-Path $project -Leaf
$backup = Join-Path (Split-Path $project -Parent) ($folder + '.legacy-agent-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
Write-Host ('项目：' + $project)
Write-Host ('备份：' + $backup)
foreach ($rel in $present) {
    Write-Host ('备份并移出：' + $rel)
    if (-not $DryRun) {
        $dest = Join-Path $backup $rel
        New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
        Move-Item -LiteralPath (Join-Path $project $rel) -Destination $dest -Force
    }
}
if ($DryRun) { Write-Host 'DryRun 完成，未更改任何文件。' }
else { Write-Host '完成。旧文件保存在项目目录之外，没有修改 DSH Profile 或系统中的其他应用。' }

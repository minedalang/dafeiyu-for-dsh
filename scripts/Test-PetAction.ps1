# Local integration test for the DaFeiYu v8.1 DSH action consumer.
# Does NOT send anything to an API, operate the mouse, or access the browser.
# Start both the DaFeiYu source build and DSH, and enable DSH linkage first.
$ErrorActionPreference = "Stop"
$base = Join-Path $env:APPDATA "dsh-pet-bridge"
$acks = Join-Path $base "acks"
New-Item -ItemType Directory -Path $acks -Force | Out-Null
$id = [guid]::NewGuid().ToString("D")
$eventFile = Join-Path $base ("dsh-diagnostic-{0}.jsonl" -f $PID)
$utf8 = New-Object System.Text.UTF8Encoding($false)
# Allow the file tailer to register this freshly created file at EOF first.
[System.IO.File]::WriteAllText($eventFile, "", $utf8)
Write-Host "Created temporary test stream. Waiting for the pet's watcher..."
Start-Sleep -Seconds 3
$ev = @{
  ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
  agent = 'dsh'
  event = 'pet/action'
  action = 'express'
  mood = 'happy'
  speech = 'this is action test!'
  inst = ([guid]::NewGuid().ToString("D"))
  requestId = $id
} | ConvertTo-Json -Compress
[System.IO.File]::AppendAllText($eventFile, $ev + "`n", $utf8)
Write-Host "Sent local event requestId=$id"
$ack = Join-Path $acks ($id + ".json")
$found = $false
for ($i=0; $i -lt 48; $i++) {
  if (Test-Path -LiteralPath $ack) {
    $receipt = Get-Content -LiteralPath $ack -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host ("Pet reply: status={0}, detail={1}" -f $receipt.status, $receipt.detail)
    $found = $true
    Remove-Item -LiteralPath $ack -Force -ErrorAction SilentlyContinue
    break
  }
  Start-Sleep -Milliseconds 250
}
Remove-Item -LiteralPath $eventFile -Force -ErrorAction SilentlyContinue
if (-not $found) {
  Write-Warning "No pet ack within 12 seconds. Confirm the v8.1 source build is actually running, DSH linkage is enabled, the pet is visible and the runtime uses this APPDATA: $base"
  exit 2
}
if ($receipt.status -ne "accepted") { exit 1 }

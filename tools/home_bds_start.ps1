# 2/2：掛包設定 + 防火牆 + 背景啟動 + 驗證
$ErrorActionPreference = 'Stop'
$root = 'E:\mc-bedrock-home'
$world = Join-Path $root 'worlds\pokemon'
New-Item -ItemType Directory -Force -Path $world | Out-Null

$wrp = '[{"pack_id":"3a0c853a-258b-5980-ad0b-1ee17cfd3c54","version":[5,0,0]}]'
$wbp = '[{"pack_id":"b3ca5287-acf7-577e-b046-bca0babb7e6d","version":[5,0,0]}]'
[IO.File]::WriteAllText((Join-Path $world 'world_resource_packs.json'), $wrp, (New-Object System.Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $world 'world_behavior_packs.json'), $wbp, (New-Object System.Text.UTF8Encoding($false)))
Write-Output '世界已掛上 RP 5.0.0 + BP 5.0.0'

foreach ($port in 19132, 19133, 7551) {
    $name = "Minecraft BDS LAN UDP $port"
    Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol UDP `
        -LocalPort $port -RemoteAddress 192.168.11.0/24 -Profile Any | Out-Null
}
Write-Output '防火牆：19132 / 19133 / 7551 UDP 只放行 192.168.11.0/24'

Get-Process bedrock_server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$logDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Start-Process -FilePath (Join-Path $root 'bedrock_server.exe') -WorkingDirectory $root `
    -RedirectStandardOutput (Join-Path $logDir 'out.log') `
    -RedirectStandardError (Join-Path $logDir 'err.log') -WindowStyle Hidden
Start-Sleep -Seconds 30

Write-Output '--- 啟動日誌 ---'
Get-Content (Join-Path $logDir 'out.log') -Tail 14
Write-Output '--- 錯誤日誌 ---'
if (Test-Path (Join-Path $logDir 'err.log')) { Get-Content (Join-Path $logDir 'err.log') -Tail 5 }
Write-Output '--- 監聽埠（UDP）---'
Get-NetUDPEndpoint -LocalPort 19132, 19133, 7551 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort | Sort-Object LocalPort | Format-Table -HideTableHeaders
Write-Output '--- 程序 ---'
Get-Process bedrock_server -ErrorAction SilentlyContinue | Select-Object Id, StartTime | Format-Table -HideTableHeaders

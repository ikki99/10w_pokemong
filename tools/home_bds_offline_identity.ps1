# 家裡這台切成 online-mode=false（只給內網、公網摸不到），讓分屏「客人」能進來
$ErrorActionPreference = 'Stop'
$root = 'E:\mc-bedrock-home'
$props = Join-Path $root 'server.properties'

$text = [IO.File]::ReadAllText($props)
$text = $text.TrimStart([char]0xFEFF)
$text = [regex]::Replace($text, '(?m)^online-mode=.*$', 'online-mode=false')
[IO.File]::WriteAllText($props, $text, (New-Object System.Text.UTF8Encoding($false)))
Write-Output '--- 目前關鍵設定 ---'
Select-String -Path $props -Pattern '^(online-mode|allow-list|enable-lan-visibility|transport|server-port|level-name|max-players)=' | ForEach-Object { '  ' + $_.Line }

# 確認防火牆仍只放行內網
Get-NetFirewallRule -DisplayName 'Minecraft BDS LAN UDP *' | Select-Object DisplayName, Enabled | Format-Table -HideTableHeaders

# 重啟
& cmd /c "schtasks /End /TN `"Minecraft Home BDS`" >nul 2>nul"
Get-Process bedrock_server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Remove-Item (Join-Path $root 'logs\out.log') -ErrorAction SilentlyContinue
& cmd /c "schtasks /Run /TN `"Minecraft Home BDS`" >nul 2>nul"
Start-Sleep -Seconds 38
Write-Output '--- 啟動結果 ---'
Select-String -Path (Join-Path $root 'logs\out.log') -Pattern 'Server started|online-mode|Accepting clients' | ForEach-Object { '  ' + $_.Line }
Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 19132, 7551 } | Select-Object LocalAddress, LocalPort | Format-Table -HideTableHeaders

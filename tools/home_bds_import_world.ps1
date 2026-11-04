# 把東京 dev 世界的存檔換成家裡這台的 pokemon 世界
$ErrorActionPreference = 'Stop'
$root = 'E:\mc-bedrock-home'
$world = Join-Path $root 'worlds\pokemon'
$incoming = Join-Path $root 'worlds\_incoming\devworld'

if (-not (Test-Path $incoming)) { throw "找不到傳過來的世界: $incoming" }

# 1) 停掉目前的家裡伺服器
& cmd /c "schtasks /End /TN `"Minecraft Home BDS`" >nul 2>nul"
Get-Process bedrock_server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# 2) 換掉世界
if (Test-Path $world) { Rename-Item $world "pokemon_fresh_$(Get-Date -Format yyyyMMdd_HHmmss)" }
Move-Item $incoming $world
Write-Output ("世界已換上東京存檔，檔案數: {0}" -f (Get-ChildItem $world -Recurse -File).Count)

# 3) 修正包版本（家裡是 5.0.0）
$wrp = '[{"pack_id":"3a0c853a-258b-5980-ad0b-1ee17cfd3c54","version":[5,0,0]}]'
$wbp = '[{"pack_id":"b3ca5287-acf7-577e-b046-bca0babb7e6d","version":[5,0,0]}]'
$enc = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $world 'world_resource_packs.json'), $wrp, $enc)
[IO.File]::WriteAllText((Join-Path $world 'world_behavior_packs.json'), $wbp, $enc)

# 4) 啟動並驗證
$logDir = Join-Path $root 'logs'
Remove-Item (Join-Path $logDir 'out.log') -ErrorAction SilentlyContinue
& cmd /c "schtasks /Run /TN `"Minecraft Home BDS`" >nul 2>nul"
Start-Sleep -Seconds 40
Write-Output '--- 日誌尾 ---'
Get-Content (Join-Path $logDir 'out.log') -Tail 10
Write-Output '--- 是否新建世界（不該出現 CREATING VANILLA WORLD）---'
(Select-String -Path (Join-Path $logDir 'out.log') -Pattern 'CREATING VANILLA WORLD').Count
Write-Output '--- 程序與埠 ---'
Get-Process bedrock_server -ErrorAction SilentlyContinue | Select-Object Id | Format-Table -HideTableHeaders
Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 19132, 7551 } | Select-Object LocalAddress, LocalPort | Format-Table -HideTableHeaders

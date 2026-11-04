# 設定 jhome 本機 BDS：online-mode 保持 true、掛上寶可夢包、只對內網開放、背景啟動
$ErrorActionPreference = 'Stop'
$root = 'E:\mc-bedrock-home'
$props = Join-Path $root 'server.properties'

# 1) 收拾剛才 --version 誤啟動的殘留程序
Get-Process bedrock_server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# 2) 把寶可夢包放到 packs 目錄（稍早由 tar 解到 staging）
foreach ($pair in @(@('staging\bp', 'behavior_packs\pokemon_bp'), @('staging\rp', 'resource_packs\pokemon_rp'))) {
    $src = Join-Path $root $pair[0]
    $dst = Join-Path $root $pair[1]
    if (Test-Path $src) {
        if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
        Move-Item $src $dst
        Write-Output ("包已就位: {0}（{1} 個檔案）" -f $pair[1], (Get-ChildItem $dst -Recurse -File).Count)
    }
}

# 3) 改 server.properties（逐項覆蓋，缺的補上）
$want = [ordered]@{
    'server-name'                     = 'Pokemon Home'
    'gamemode'                        = 'survival'
    'difficulty'                      = 'normal'
    'allow-cheats'                    = 'false'
    'max-players'                     = '10'
    'online-mode'                     = 'true'
    'allow-list'                      = 'false'
    'server-port'                     = '19132'
    'server-portv6'                   = '19133'
    'level-name'                      = 'pokemon'
    'level-seed'                      = ''
    'view-distance'                   = '12'
    'tick-distance'                   = '4'
    'player-idle-timeout'             = '0'
    'default-player-permission-level' = 'member'
    'texturepack-required'            = 'false'
    'compression-threshold'           = '1'
    'client-side-chunk-generation-enabled' = 'true'
}
$lines = Get-Content $props
foreach ($k in $want.Keys) {
    $v = $want[$k]
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^$([regex]::Escape($k))=") { $lines[$i] = "$k=$v"; $found = $true }
    }
    if (-not $found) { $lines += "$k=$v" }
}
Set-Content -Path $props -Value $lines -Encoding UTF8
Write-Output 'server.properties 已更新：'
Select-String -Path $props -Pattern '^(server-name|online-mode|allow-list|server-port|server-portv6|level-name|gamemode|max-players|transport)=' | ForEach-Object { '  ' + $_.Line }

# 4) 建世界目錄並掛包（開機前先寫好，第一次啟動就帶包）
$world = Join-Path $root 'worlds\pokemon'
New-Item -ItemType Directory -Force -Path $world | Out-Null
$rpManifest = Get-Content (Join-Path $root 'resource_packs\pokemon_rp\manifest.json') -Raw | ConvertFrom-Json
$bpManifest = Get-Content (Join-Path $root 'behavior_packs\pokemon_bp\manifest.json') -Raw | ConvertFrom-Json
@(@{ pack_id = $rpManifest.header.uuid; version = $rpManifest.header.version }) | ConvertTo-Json -AsArray | Set-Content (Join-Path $world 'world_resource_packs.json') -Encoding UTF8
@(@{ pack_id = $bpManifest.header.uuid; version = $bpManifest.header.version }) | ConvertTo-Json -AsArray | Set-Content (Join-Path $world 'world_behavior_packs.json') -Encoding UTF8
Write-Output ("RP {0} / BP {1} 已寫入世界設定" -f $rpManifest.header.version -join '.', ($bpManifest.header.version -join '.'))

# 5) 防火牆：只放行內網 192.168.11.0/24 的 UDP
foreach ($port in 19132, 19133, 7551) {
    $name = "Minecraft BDS LAN UDP $port"
    Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol UDP `
        -LocalPort $port -RemoteAddress 192.168.11.0/24 -Profile Any | Out-Null
}
Write-Output '防火牆規則：19132 / 19133 / 7551 UDP，來源限定 192.168.11.0/24'

# 6) 背景啟動（關掉 SSH 也不會停）
$logDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Start-Process -FilePath (Join-Path $root 'bedrock_server.exe') -WorkingDirectory $root `
    -RedirectStandardOutput (Join-Path $logDir 'out.log') `
    -RedirectStandardError (Join-Path $logDir 'err.log') -WindowStyle Hidden
Start-Sleep -Seconds 25
Write-Output '--- 啟動日誌 ---'
Get-Content (Join-Path $logDir 'out.log') -Tail 12
Write-Output '--- 監聽埠 ---'
Get-NetUDPEndpoint -LocalPort 19132, 19133, 7551 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort | Format-Table -HideTableHeaders
Get-Process bedrock_server -ErrorAction SilentlyContinue | Select-Object Id, ProcessName | Format-Table -HideTableHeaders

param(
  [string]$Root = 'E:\mc-bedrock-home',
  [string]$Staging = 'E:\mc-bedrock-home\staging2'
)
$ErrorActionPreference = 'Stop'
$enc = New-Object System.Text.UTF8Encoding($false)
$BP_UUID = 'b3ca5287-acf7-577e-b046-bca0babb7e6d'
$RP_UUID = '3a0c853a-258b-5980-ad0b-1ee17cfd3c54'
$world = Join-Path $Root 'worlds\pokemon'

if (-not (Test-Path (Join-Path $Staging 'bp'))) { throw "找不到 staging2\bp，先上傳" }

Write-Output '=== 1. 停服 ==='
& cmd /c "schtasks /End /TN `"Minecraft Home BDS`" >nul 2>nul"
Get-Process bedrock_server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 4

Write-Output '=== 2. 備份 + 替換 ==='
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
foreach ($pair in @(@('bp', 'behavior_packs\pokemon_bp'), @('rp', 'resource_packs\pokemon_rp'))) {
  $src = Join-Path $Staging $pair[0]
  $dst = Join-Path $Root $pair[1]
  if (-not (Test-Path (Join-Path $src 'manifest.json'))) { throw "staging 缺少 $($pair[0])\manifest.json" }
  if (Test-Path $dst) {
    $bak = "$dst-OLD-$stamp"
    Move-Item $dst $bak -Force
  }
  Copy-Item $src $dst -Recurse -Force
  Write-Output ("  {0}: {1} 個檔案" -f $pair[1], (Get-ChildItem $dst -Recurse -File).Count)
}

Write-Output '=== 3. 寫世界包清單 ==='
$bpv = @((Get-Content (Join-Path $Root 'behavior_packs\pokemon_bp\manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json).header.version)
$rpv = @((Get-Content (Join-Path $Root 'resource_packs\pokemon_rp\manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json).header.version)
$bpJson = ConvertTo-Json -Compress -Depth 5 -InputObject @(@{ pack_id = $BP_UUID; version = $bpv })
$rpJson = ConvertTo-Json -Compress -Depth 5 -InputObject @(@{ pack_id = $RP_UUID; version = $rpv })
[IO.File]::WriteAllText((Join-Path $world 'world_behavior_packs.json'), $bpJson, $enc)
[IO.File]::WriteAllText((Join-Path $world 'world_resource_packs.json'), $rpJson, $enc)
Write-Output ("  BP {0}  RP {1}" -f ($bpv -join '.'), ($rpv -join '.'))
Write-Output "  $bpJson"
Write-Output "  $rpJson"

Write-Output '=== 4. 啟動 ==='
Remove-Item (Join-Path $Root 'logs\out.log') -ErrorAction SilentlyContinue
& cmd /c "schtasks /Run /TN `"Minecraft Home BDS`" >nul 2>nul"
Start-Sleep -Seconds 45
Get-Content (Join-Path $Root 'logs\out.log') -ErrorAction SilentlyContinue -Tail 60 |
  Select-String -Pattern 'module loaded|Server started|Pack Stack|ERROR|Exception' |
  Select-Object -Last 6 | ForEach-Object { '  ' + $_.Line.Substring(0, [Math]::Min(170, $_.Line.Length)) }

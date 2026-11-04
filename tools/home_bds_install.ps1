# 第一檔：在 jhome（Windows，有線 192.168.11.4）裝一份本機 BDS
$ErrorActionPreference = 'Stop'
$root = 'E:\mc-bedrock-home'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$zip = Join-Path $root 'bds.zip'
$url = 'https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.26.61.1.zip'

if (-not (Test-Path $zip) -or (Get-Item $zip).Length -lt 80000000) {
    $ProgressPreference = 'SilentlyContinue'
    Write-Output "下載中: $url"
    curl.exe -L -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' -o $zip $url
}
Write-Output ("zip 大小: {0:N1} MB" -f ((Get-Item $zip).Length / 1MB))

if (-not (Test-Path (Join-Path $root 'bedrock_server.exe'))) {
    Write-Output '解壓中…'
    Expand-Archive -Path $zip -DestinationPath $root -Force
}
Write-Output '--- 目錄內容（前 20 項）---'
Get-ChildItem $root | Select-Object -First 20 Name, Length | Format-Table -HideTableHeaders
Write-Output '--- 版本 ---'
& (Join-Path $root 'bedrock_server.exe') --version 2>&1 | Select-Object -First 3

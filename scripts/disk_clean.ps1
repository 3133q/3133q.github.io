$ErrorActionPreference = "SilentlyContinue"

function Get-SizeMB($p) {
  if (Test-Path $p) {
    return ((Get-ChildItem $p -Recurse -Force -File | Measure-Object -Property Length -Sum).Sum / 1MB)
  }
  return 0
}

# 1. Recycle Bin
Clear-RecycleBin -Force
Write-Output "[done] RecycleBin cleared"

# 2. Temp
$temp = $env:TEMP
$before = Get-SizeMB $temp
Get-ChildItem $temp -Recurse -Force | Remove-Item -Recurse -Force
$after = Get-SizeMB $temp
Write-Output ("[done] Temp: freed {0:N1} MB" -f ($before - $after))

# 3. Browser + pip caches
$targets = @(
  "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
  "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
  "$env:LOCALAPPDATA\pip\cache",
  "$env:LOCALAPPDATA\CrashDumps"
)
foreach ($t in $targets) {
  $b = Get-SizeMB $t
  Get-ChildItem $t -Recurse -Force | Remove-Item -Recurse -Force
  $a = Get-SizeMB $t
  Write-Output ("[done] {0}: freed {1:N1} MB" -f $t, ($b - $a))
}

# 4. AI tool caches
foreach ($t in @("$env:USERPROFILE\.cache\codex-runtimes", "$env:USERPROFILE\.cache\opencode")) {
  $b = Get-SizeMB $t
  Remove-Item $t -Recurse -Force
  $a = Get-SizeMB $t
  Write-Output ("[done] {0}: freed {1:N1} MB" -f $t, ($b - $a))
}

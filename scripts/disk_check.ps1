$paths = @(
  "$env:TEMP",
  "C:\Windows\Temp",
  "C:\Windows\SoftwareDistribution\Download",
  "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
  "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
  "$env:LOCALAPPDATA\pip\cache",
  "$env:APPDATA\npm-cache",
  "$env:USERPROFILE\.cache",
  "C:\Windows\Logs\CBS",
  "$env:LOCALAPPDATA\CrashDumps"
)
foreach ($p in $paths) {
  if (Test-Path $p) {
    $size = (Get-ChildItem $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    "{0,12:N1} MB  {1}" -f ($size/1MB), $p
  }
}

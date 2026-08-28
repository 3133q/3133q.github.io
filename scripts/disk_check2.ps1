# Recycle Bin size
$shell = New-Object -ComObject Shell.Application
$recycle = $shell.NameSpace(10)
$sum = 0
foreach ($item in $recycle.Items()) { $sum += $item.Size }
"{0,12:N1} MB  RecycleBin" -f ($sum/1MB)

# .cache subdirectories
Get-ChildItem "$env:USERPROFILE\.cache" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $s = (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  "{0,12:N1} MB  .cache\{1}" -f ($s/1MB), $_.Name
}

# hibernation / pagefile
foreach ($f in @("C:\hiberfil.sys", "C:\pagefile.sys", "C:\swapfile.sys")) {
  if (Test-Path $f) {
    $s = (Get-Item $f -Force).Length
    "{0,12:N1} MB  {1}" -f ($s/1MB), $f
  }
}

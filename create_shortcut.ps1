$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AI Code Converter.lnk"
$TargetFile = Join-Path $PWD "start.bat"
$IconFile = Join-Path $PWD "frontend\public\favicon.ico"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = $PWD.Path
$Shortcut.Description = "Start AI Multi-Code Converter"

if (Test-Path $IconFile) {
    $Shortcut.IconLocation = "$IconFile"
}

$Shortcut.Save()

Write-Host "Shortcut created successfully on Desktop!"
Start-Sleep -Seconds 3

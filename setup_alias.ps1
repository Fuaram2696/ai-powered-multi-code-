$ProfilePath = $PROFILE
$ProjectDir = $PWD
$StartBat = Join-Path $ProjectDir "start.bat"

# Create profile if it doesn't exist
if (-not (Test-Path $ProfilePath)) {
    New-Item -ItemType File -Path $ProfilePath -Force
}

# Check if alias already exists
$ProfileContent = Get-Content $ProfilePath -Raw
if ($ProfileContent -match "function ai-code") {
    Write-Host "Alias 'ai-code' already exists in profile."
}
else {
    $FunctionDef = "
function ai-code {
    Start-Process -FilePath `"$StartBat`"
}
"
    Add-Content -Path $ProfilePath -Value $FunctionDef
    Write-Host "Success! Added 'ai-code' command to your PowerShell profile."
    Write-Host "Please restart your terminal or run '. `$PROFILE' to use it."
}

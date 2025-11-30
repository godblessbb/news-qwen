# Conda Full Auto Migration Script (C: to D:)
# ONE-CLICK complete migration

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Conda AUTO Migration Tool (C: -> D:)" -ForegroundColor Cyan
Write-Host "This will AUTOMATICALLY migrate your conda to D: drive" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Export all your current environments" -ForegroundColor White
Write-Host "  2. Download Miniconda installer" -ForegroundColor White
Write-Host "  3. Install Miniconda to D:\miniconda3" -ForegroundColor White
Write-Host "  4. Restore all environments" -ForegroundColor White
Write-Host "  5. Guide you to delete old C: installation" -ForegroundColor White
Write-Host ""
Write-Host "Estimated time: 20-40 minutes" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "Continue with automatic migration? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Migration cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "PHASE 1: Export Current Environments" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Get current conda base
$oldCondaBase = ""
try {
    $oldCondaBase = (conda info --base).Trim()
    Write-Host "Current conda location: $oldCondaBase" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Conda not found" -ForegroundColor Red
    exit 1
}

# Create backup directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\conda_backup_$timestamp"
Write-Host "Creating backup: $backupDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# List and export environments
Write-Host "Listing environments..." -ForegroundColor Cyan
conda env list

$envList = conda env list
$envs = @()
foreach ($line in $envList) {
    if ($line -match '^(\w[\w\-]+)\s+') {
        $envName = $matches[1]
        if ($envName -ne "base") {
            $envs += $envName
        }
    }
}

Write-Host ""
Write-Host "Found $($envs.Count) environment(s) to export" -ForegroundColor Green
Write-Host ""

# Export each environment
foreach ($envName in $envs) {
    Write-Host "Exporting: $envName" -ForegroundColor Cyan
    $ymlFile = Join-Path $backupDir "$envName.yml"
    conda env export -n $envName > $ymlFile 2>$null
    Write-Host "  Saved to: $ymlFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "Phase 1 Complete!" -ForegroundColor Green
Write-Host ""

# Phase 2: Download Miniconda
Write-Host "============================================================" -ForegroundColor Green
Write-Host "PHASE 2: Download Miniconda Installer" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$installerPath = "$env:TEMP\Miniconda3-latest-Windows-x86_64.exe"
$downloadUrl = "https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe"

if (Test-Path $installerPath) {
    Write-Host "Installer already exists" -ForegroundColor Yellow
} else {
    Write-Host "Downloading Miniconda..." -ForegroundColor Cyan
    Write-Host "URL: $downloadUrl" -ForegroundColor White
    Write-Host "This may take 5-10 minutes, please wait..." -ForegroundColor Yellow
    Write-Host ""

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath
        Write-Host "Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "Download failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually and press Enter to continue" -ForegroundColor Yellow
        Write-Host "URL: $downloadUrl"
        Write-Host "Save to: $installerPath"
        Read-Host "Press Enter after download"
    }
}

if (-not (Test-Path $installerPath)) {
    Write-Host "Error: Installer not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Phase 2 Complete!" -ForegroundColor Green
Write-Host ""

# Phase 3: Install Miniconda
Write-Host "============================================================" -ForegroundColor Green
Write-Host "PHASE 3: Install Miniconda to D:\miniconda3" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$targetPath = "D:\miniconda3"
if (Test-Path $targetPath) {
    Write-Host "WARNING: D:\miniconda3 already exists!" -ForegroundColor Red
    $timestamp2 = Get-Date -Format "yyyyMMdd_HHmmss"
    $oldPath = "D:\miniconda3_old_$timestamp2"
    Write-Host "Renaming to: $oldPath" -ForegroundColor Yellow
    Rename-Item $targetPath $oldPath
}

Write-Host "Installing Miniconda..." -ForegroundColor Cyan
Write-Host "This will take 3-5 minutes, please wait..." -ForegroundColor Yellow
Write-Host "DO NOT CLOSE THIS WINDOW!" -ForegroundColor Red
Write-Host ""

$installArgs = @(
    "/S",
    "/InstallationType=JustMe",
    "/RegisterPython=1",
    "/AddToPath=1",
    "/D=$targetPath"
)

Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow

if (Test-Path "$targetPath\Scripts\conda.exe") {
    Write-Host "Installation successful!" -ForegroundColor Green
} else {
    Write-Host "Error: Installation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Phase 3 Complete!" -ForegroundColor Green
Write-Host ""

# Update PATH for current session
$env:PATH = "$targetPath;$targetPath\Scripts;$targetPath\Library\bin;" + $env:PATH

# Initialize conda
Write-Host "Initializing conda..." -ForegroundColor Cyan
& "$targetPath\Scripts\conda.exe" init powershell | Out-Null
Write-Host "Conda initialized" -ForegroundColor Green
Write-Host ""

# Phase 4: Restore Environments
Write-Host "============================================================" -ForegroundColor Green
Write-Host "PHASE 4: Restore All Environments" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Restoring $($envs.Count) environment(s)..." -ForegroundColor Cyan
Write-Host "This may take 15-30 minutes total" -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$failedEnvs = @()

foreach ($envName in $envs) {
    Write-Host "[$($successCount + 1)/$($envs.Count)] Restoring: $envName" -ForegroundColor Cyan
    $ymlFile = Join-Path $backupDir "$envName.yml"

    & "$targetPath\Scripts\conda.exe" env create -f $ymlFile 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS: $envName" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  FAILED: $envName" -ForegroundColor Red
        $failedEnvs += $envName
    }
}

Write-Host ""
Write-Host "Phase 4 Complete!" -ForegroundColor Green
Write-Host "  Successful: $successCount" -ForegroundColor Green
if ($failedEnvs.Count -gt 0) {
    Write-Host "  Failed: $($failedEnvs.Count)" -ForegroundColor Red
    Write-Host "  Failed environments: $($failedEnvs -join ', ')" -ForegroundColor Yellow
}
Write-Host ""

# Final Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "MIGRATION COMPLETE!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Old location: $oldCondaBase" -ForegroundColor White
Write-Host "  New location: $targetPath" -ForegroundColor White
Write-Host "  Backup: $backupDir" -ForegroundColor White
Write-Host "  Environments restored: $successCount / $($envs.Count)" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. CLOSE this PowerShell window" -ForegroundColor Cyan
Write-Host "2. OPEN a NEW PowerShell window" -ForegroundColor Cyan
Write-Host "3. Verify installation:" -ForegroundColor Cyan
Write-Host "   conda info --base" -ForegroundColor White
Write-Host "   (should show: D:\miniconda3)" -ForegroundColor White
Write-Host ""
Write-Host "4. For news-qwen environment, reinstall PyTorch:" -ForegroundColor Cyan
Write-Host "   conda activate news-qwen" -ForegroundColor White
Write-Host "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor White
Write-Host ""
Write-Host "5. After verification, delete old conda:" -ForegroundColor Cyan
Write-Host "   Remove-Item -Recurse -Force $oldCondaBase" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

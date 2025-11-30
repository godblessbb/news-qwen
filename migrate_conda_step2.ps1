# Conda Full Migration Script - Step 2: Download and Install
# Run this AFTER migrate_conda.ps1

param(
    [string]$BackupDir = ""
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Conda Migration - Step 2: Download and Install" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Find the latest backup directory if not specified
if ($BackupDir -eq "") {
    $backups = Get-ChildItem "D:\conda_backup_*" -Directory | Sort-Object Name -Descending
    if ($backups.Count -eq 0) {
        Write-Host "Error: No backup directory found!" -ForegroundColor Red
        Write-Host "Please run migrate_conda.ps1 first" -ForegroundColor Yellow
        exit 1
    }
    $BackupDir = $backups[0].FullName
    Write-Host "Using backup: $BackupDir" -ForegroundColor Green
} else {
    if (-not (Test-Path $BackupDir)) {
        Write-Host "Error: Backup directory not found: $BackupDir" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 1: Download Miniconda
Write-Host "Step 1: Download Miniconda installer" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$installerPath = "$env:TEMP\Miniconda3-latest-Windows-x86_64.exe"
$downloadUrl = "https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe"

if (Test-Path $installerPath) {
    Write-Host "Installer already exists: $installerPath" -ForegroundColor Yellow
    $redownload = Read-Host "Re-download? (y/n)"
    if ($redownload -eq "y") {
        Remove-Item $installerPath -Force
    }
}

if (-not (Test-Path $installerPath)) {
    Write-Host "Downloading from Tsinghua mirror..." -ForegroundColor Cyan
    Write-Host "URL: $downloadUrl"
    Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath
        Write-Host "Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "Download failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually from:" -ForegroundColor Yellow
        Write-Host "  $downloadUrl"
        Write-Host "Save to: $installerPath"
        Read-Host "Press Enter after manual download"

        if (-not (Test-Path $installerPath)) {
            Write-Host "Installer not found. Exiting." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""

# Step 2: Check if D:\miniconda3 already exists
Write-Host "Step 2: Check installation location" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$targetPath = "D:\miniconda3"
if (Test-Path $targetPath) {
    Write-Host "WARNING: D:\miniconda3 already exists!" -ForegroundColor Red
    Write-Host "This will be the NEW conda installation location." -ForegroundColor Yellow
    $action = Read-Host "Options: [R]ename old, [D]elete old, [A]bort? (r/d/a)"

    if ($action -eq "r") {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $oldPath = "D:\miniconda3_old_$timestamp"
        Write-Host "Renaming to: $oldPath" -ForegroundColor Cyan
        Rename-Item $targetPath $oldPath
        Write-Host "Renamed successfully" -ForegroundColor Green
    } elseif ($action -eq "d") {
        Write-Host "Deleting old installation..." -ForegroundColor Yellow
        Remove-Item $targetPath -Recurse -Force
        Write-Host "Deleted successfully" -ForegroundColor Green
    } else {
        Write-Host "Installation aborted" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""

# Step 3: Install Miniconda silently
Write-Host "Step 3: Install Miniconda to D:\miniconda3" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
Write-Host "Installing... This may take 3-5 minutes" -ForegroundColor Yellow
Write-Host "Please wait, DO NOT close this window!" -ForegroundColor Red
Write-Host ""

$installArgs = @(
    "/S",  # Silent install
    "/InstallationType=JustMe",
    "/RegisterPython=1",
    "/AddToPath=1",
    "/D=$targetPath"
)

try {
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow
    Write-Host "Installation complete!" -ForegroundColor Green
} catch {
    Write-Host "Installation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Verify installation
Write-Host "Step 4: Verify installation" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

if (Test-Path "$targetPath\Scripts\conda.exe") {
    Write-Host "Conda installed successfully at: $targetPath" -ForegroundColor Green
} else {
    Write-Host "Error: Conda not found at expected location" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Update PATH for current session
Write-Host "Step 5: Update environment for current session" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$env:PATH = "$targetPath;$targetPath\Scripts;$targetPath\Library\bin;" + $env:PATH
Write-Host "PATH updated for current session" -ForegroundColor Green
Write-Host ""

# Step 6: Initialize conda
Write-Host "Step 6: Initialize conda" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

& "$targetPath\Scripts\conda.exe" init powershell
Write-Host "Conda initialized" -ForegroundColor Green
Write-Host ""

# Step 7: Verify conda works
Write-Host "Step 7: Verify conda installation" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$condaBase = & "$targetPath\Scripts\conda.exe" info --base
Write-Host "Conda base: $condaBase" -ForegroundColor Cyan

if ($condaBase -like "*$targetPath*") {
    Write-Host "SUCCESS: Conda is now using D:\miniconda3" -ForegroundColor Green
} else {
    Write-Host "Warning: Conda base path unexpected" -ForegroundColor Yellow
}

Write-Host ""

# Step 8: Ask to restore environments
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Restore your environments" -ForegroundColor Yellow
Write-Host "Backup location: $BackupDir" -ForegroundColor Cyan
Write-Host ""

$restore = Read-Host "Restore environments now? (y/n)"
if ($restore -eq "y") {
    Write-Host ""
    Write-Host "Starting environment restoration..." -ForegroundColor Cyan

    # Find all .yml files in backup
    $ymlFiles = Get-ChildItem "$BackupDir\*.yml"

    if ($ymlFiles.Count -eq 0) {
        Write-Host "No environment files found in backup" -ForegroundColor Yellow
    } else {
        Write-Host "Found $($ymlFiles.Count) environment(s) to restore" -ForegroundColor Green
        Write-Host ""

        foreach ($ymlFile in $ymlFiles) {
            $envName = [System.IO.Path]::GetFileNameWithoutExtension($ymlFile.Name)
            Write-Host "Restoring environment: $envName" -ForegroundColor Cyan
            Write-Host "This may take 5-15 minutes..." -ForegroundColor Yellow

            & "$targetPath\Scripts\conda.exe" env create -f $ymlFile.FullName

            if ($LASTEXITCODE -eq 0) {
                Write-Host "  SUCCESS: $envName restored" -ForegroundColor Green
            } else {
                Write-Host "  FAILED: $envName restoration failed" -ForegroundColor Red
                Write-Host "  You can restore manually later with:" -ForegroundColor Yellow
                Write-Host "  conda env create -f $($ymlFile.FullName)" -ForegroundColor Cyan
            }
            Write-Host ""
        }

        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "Environment Restoration Complete!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""

        # Special note for news-qwen
        Write-Host "IMPORTANT: For news-qwen environment" -ForegroundColor Yellow
        Write-Host "You need to reinstall PyTorch CUDA version:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  conda activate news-qwen" -ForegroundColor Cyan
        Write-Host "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor Cyan
        Write-Host ""
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Migration Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Please close and reopen PowerShell" -ForegroundColor Yellow
Write-Host "Then verify with: conda info --base" -ForegroundColor Cyan
Write-Host "Should show: D:\miniconda3" -ForegroundColor Cyan
Write-Host ""
Write-Host "After verification, you can delete old C:\Users\user\miniconda3" -ForegroundColor Yellow
Write-Host ""

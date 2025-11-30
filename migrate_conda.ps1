# Conda Environment Migration Script (C: to D:)
# Simple version without encoding issues

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Conda Environment Migration Tool (C: -> D:)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check current environment
$currentEnv = $env:CONDA_DEFAULT_ENV
if ($currentEnv -and $currentEnv -ne "base") {
    Write-Host "Warning: Currently in environment '$currentEnv'" -ForegroundColor Yellow
    Write-Host "Please run: conda deactivate" -ForegroundColor Yellow
    $continue = Read-Host "Continue? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# Step 1: List all environments
Write-Host ""
Write-Host "Step 1: List all Conda environments" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
conda env list
Write-Host ""

# Step 2: Create backup directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\conda_backup_$timestamp"
Write-Host "Step 2: Create backup directory" -ForegroundColor Green
Write-Host "Backup location: $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "Backup directory created successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Get all environment names
Write-Host "Step 3: Export all environment configurations" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

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

Write-Host "Found $($envs.Count) environment(s) to export"
Write-Host ""

# Step 4: Export each environment
foreach ($envName in $envs) {
    Write-Host "Exporting environment: $envName" -ForegroundColor Cyan

    $ymlFile = Join-Path $backupDir "$envName.yml"
    conda env export -n $envName > $ymlFile 2>$null
    Write-Host "  Exported to: $ymlFile" -ForegroundColor Green

    $reqFile = Join-Path $backupDir "$envName-requirements.txt"
    conda run -n $envName pip freeze > $reqFile 2>$null
    Write-Host "  Pip packages: $reqFile" -ForegroundColor Green
    Write-Host ""
}

# Step 5: Backup conda config
Write-Host "Step 4: Backup Conda configuration" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$condarcPath = Join-Path $env:USERPROFILE ".condarc"
if (Test-Path $condarcPath) {
    $condarcBackup = Join-Path $backupDir "condarc_backup.txt"
    Copy-Item $condarcPath $condarcBackup -Force
    Write-Host ".condarc backed up" -ForegroundColor Green
}

$condaInfoFile = Join-Path $backupDir "conda_info.txt"
conda info --base > $condaInfoFile
Write-Host "Conda info saved" -ForegroundColor Green
Write-Host ""

# Step 6: Show current path
Write-Host "Step 5: Conda installation info" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
$condaBasePath = (conda info --base).Trim()
Write-Host "Current location: $condaBasePath" -ForegroundColor Cyan
Write-Host ""

# Generate README documentation
$envList = ""
foreach ($env in $envs) {
    $envList += "- $env`n"
}

$restoreCommands = ""
foreach ($env in $envs) {
    $restoreCommands += "conda env create -f $env.yml`n"
}

$testCommands = ""
foreach ($env in $envs) {
    $testCommands += "conda activate $env`npython --version`nconda deactivate`n`n"
}

$readmeContent = @"
# Conda Environment Migration Guide

## Backup Information

- Backup time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Original location: $condaBasePath
- Target location: D:\miniconda3
- Backup directory: $backupDir

## Exported Environments

$envList

## Migration Steps

### 1. Download Miniconda

Tsinghua mirror (recommended for China):
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/

Download: Miniconda3-latest-Windows-x86_64.exe

### 2. Install to D: drive

Installation path: D:\miniconda3
Check: Add to PATH and Register as default Python

### 3. Verify new installation

Close all PowerShell windows, reopen and run:

``````
conda info --base
``````

Should show: D:\miniconda3

### 4. Restore all environments

Navigate to backup directory:

``````
cd $backupDir
``````

Restore each environment:

``````
$restoreCommands
``````

### 5. Important: PyTorch CUDA version

For news-qwen environment, reinstall PyTorch after restore:

``````
conda activate news-qwen
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
``````

### 6. Verify environments

``````
conda env list

$testCommands
``````

### 7. Delete old miniconda3

After confirming all environments work:

``````
Remove-Item -Recurse -Force $condaBasePath
``````

## Files in Backup

$envList
Each environment has:
- .yml file (complete configuration)
- requirements.txt file (pip packages)

"@

$readmePath = Join-Path $backupDir "README.txt"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "Migration guide saved to: README.txt" -ForegroundColor Green
Write-Host ""

# Complete
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Environment export complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Check backup directory: $backupDir" -ForegroundColor Cyan
Write-Host "2. Read README.txt for detailed steps" -ForegroundColor Cyan
Write-Host "3. Download Miniconda from: https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/" -ForegroundColor Cyan
Write-Host "4. Install to D:\miniconda3" -ForegroundColor Cyan
Write-Host "5. Restore environments using yml files" -ForegroundColor Cyan
Write-Host ""

$openDir = Read-Host "Open backup directory? (y/n)"
if ($openDir -eq "y") {
    explorer $backupDir
}

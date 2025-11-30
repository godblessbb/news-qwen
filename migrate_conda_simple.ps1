# Conda 环境迁移脚本 (C盘 -> D盘)
# 简化版本

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Conda 环境迁移工具 (C盘 -> D盘)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查当前环境
$currentEnv = $env:CONDA_DEFAULT_ENV
if ($currentEnv -and $currentEnv -ne "base") {
    Write-Host "警告: 当前在环境 '$currentEnv' 中" -ForegroundColor Yellow
    Write-Host "请先运行: conda deactivate" -ForegroundColor Yellow
    $continue = Read-Host "是否继续? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# 步骤 1: 列出所有环境
Write-Host ""
Write-Host "步骤 1: 列出所有 Conda 环境" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
conda env list
Write-Host ""

# 步骤 2: 创建备份目录
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\conda_backup_$timestamp"
Write-Host "步骤 2: 创建备份目录" -ForegroundColor Green
Write-Host "备份位置: $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "备份目录创建成功" -ForegroundColor Green
Write-Host ""

# 步骤 3: 获取所有环境名称
Write-Host "步骤 3: 导出所有环境配置" -ForegroundColor Green
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

Write-Host "发现 $($envs.Count) 个环境需要导出"
Write-Host ""

# 步骤 4: 导出每个环境
foreach ($envName in $envs) {
    Write-Host "正在导出环境: $envName" -ForegroundColor Cyan

    $ymlFile = Join-Path $backupDir "$envName.yml"
    conda env export -n $envName > $ymlFile 2>$null
    Write-Host "  导出到: $ymlFile" -ForegroundColor Green

    $reqFile = Join-Path $backupDir "$envName-requirements.txt"
    conda run -n $envName pip freeze > $reqFile 2>$null
    Write-Host "  pip 包列表: $reqFile" -ForegroundColor Green
    Write-Host ""
}

# 步骤 5: 备份配置
Write-Host "步骤 4: 备份 Conda 配置" -ForegroundColor Green
Write-Host "------------------------------------------------------------"

$condarcPath = Join-Path $env:USERPROFILE ".condarc"
if (Test-Path $condarcPath) {
    $condarcBackup = Join-Path $backupDir "condarc_backup.txt"
    Copy-Item $condarcPath $condarcBackup -Force
    Write-Host ".condarc 已备份" -ForegroundColor Green
}

$condaInfoFile = Join-Path $backupDir "conda_info.txt"
conda info --base > $condaInfoFile
Write-Host "Conda 信息已保存" -ForegroundColor Green
Write-Host ""

# 步骤 6: 显示当前路径
Write-Host "步骤 5: Conda 安装信息" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
$condaBasePath = (conda info --base).Trim()
Write-Host "当前安装位置: $condaBasePath" -ForegroundColor Cyan
Write-Host ""

# 生成 README 文档
$readmeContent = @"
# Conda 环境迁移说明

## 备份信息

- 备份时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 原始位置: $condaBasePath
- 目标位置: D:\miniconda3
- 备份目录: $backupDir

## 已导出的环境

$($envs | ForEach-Object { "- $_" })

## 迁移步骤

### 1. 下载 Miniconda

清华镜像: https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/
下载: Miniconda3-latest-Windows-x86_64.exe

### 2. 安装到 D 盘

安装路径: D:\miniconda3
勾选: Add to PATH 和 Register as default Python

### 3. 验证新安装

关闭所有 PowerShell 窗口，重新打开后运行:
conda info --base

应该显示: D:\miniconda3

### 4. 恢复所有环境

cd $backupDir

恢复每个环境:
$($envs | ForEach-Object { "conda env create -f $_.yml" })

### 5. 特别注意: PyTorch CUDA 版本

对于 news-qwen 环境，恢复后需要重新安装 PyTorch:

conda activate news-qwen
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

### 6. 验证环境

conda env list
$($envs | ForEach-Object { @"
conda activate $_
python --version
conda deactivate
"@ })

### 7. 删除旧的 miniconda3

确认所有环境正常后:
Remove-Item -Recurse -Force $condaBasePath

"@

$readmePath = Join-Path $backupDir "README.md"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "迁移说明已保存到: $backupDir\README.md" -ForegroundColor Green
Write-Host ""

# 完成
Write-Host "============================================================" -ForegroundColor Green
Write-Host "环境导出完成!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 查看备份目录: $backupDir" -ForegroundColor Cyan
Write-Host "2. 阅读 README.md 了解详细步骤" -ForegroundColor Cyan
Write-Host "3. 下载 Miniconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/" -ForegroundColor Cyan
Write-Host "4. 安装到 D:\miniconda3" -ForegroundColor Cyan
Write-Host "5. 使用备份的 yml 文件恢复环境" -ForegroundColor Cyan
Write-Host ""

$openDir = Read-Host "是否打开备份目录? (y/n)"
if ($openDir -eq "y") {
    explorer $backupDir
}

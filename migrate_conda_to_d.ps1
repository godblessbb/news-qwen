# ============================================================
# Conda 环境迁移脚本 (C盘 -> D盘)
# 适用于 Windows PowerShell
# ============================================================

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Conda 环境迁移工具 (C盘 -> D盘)" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# 检查是否在 base 环境
$currentEnv = $env:CONDA_DEFAULT_ENV
if ($currentEnv -and $currentEnv -ne "base") {
    Write-Host "警告: 当前在环境 '$currentEnv' 中" -ForegroundColor Yellow
    Write-Host "请先运行: conda deactivate" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "是否继续? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# ============================================================
# 步骤 1: 列出所有环境
# ============================================================
Write-Host ""
Write-Host "步骤 1: 列出所有 Conda 环境" -ForegroundColor Green
Write-Host ("-" * 60)
conda env list
Write-Host ""

# ============================================================
# 步骤 2: 创建备份目录
# ============================================================
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\conda_migration_backup_$timestamp"
Write-Host "步骤 2: 创建备份目录" -ForegroundColor Green
Write-Host "备份位置: $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "备份目录创建成功" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 3: 导出所有环境配置
# ============================================================
Write-Host "步骤 3: 导出所有环境配置" -ForegroundColor Green
Write-Host ("-" * 60)

# 获取所有环境名称（排除 base）
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

foreach ($envName in $envs) {
    Write-Host "正在导出环境: $envName" -ForegroundColor Cyan

    # 导出为 yml 文件
    $ymlFile = Join-Path $backupDir "$envName.yml"
    conda env export -n $envName > $ymlFile 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  导出到: $ymlFile" -ForegroundColor Green
    } else {
        Write-Host "  警告: 导出失败" -ForegroundColor Yellow
    }

    # 导出为 requirements.txt（备用）
    $reqFile = Join-Path $backupDir "$envName-requirements.txt"
    conda run -n $envName pip freeze > $reqFile 2>$null
    Write-Host "  pip 包列表: $reqFile" -ForegroundColor Green
    Write-Host ""
}

Write-Host "所有环境配置已导出到: $backupDir" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 4: 备份 Conda 配置
# ============================================================
Write-Host "步骤 4: 备份 Conda 配置" -ForegroundColor Green
Write-Host ("-" * 60)

# 备份 .condarc
$condarcPath = Join-Path $env:USERPROFILE ".condarc"
if (Test-Path $condarcPath) {
    $condarcBackup = Join-Path $backupDir "condarc_backup.txt"
    Copy-Item $condarcPath $condarcBackup -Force
    Write-Host ".condarc 已备份" -ForegroundColor Green
}

# 记录当前 miniconda 位置
$condaInfoFile = Join-Path $backupDir "conda_info.txt"
conda info --base > $condaInfoFile
Write-Host "Conda 信息已保存" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 5: 计算空间占用
# ============================================================
Write-Host "步骤 5: 计算当前空间占用" -ForegroundColor Green
Write-Host ("-" * 60)

$condaBasePath = (conda info --base).Trim()
Write-Host "Conda 安装位置: $condaBasePath"

if (Test-Path $condaBasePath) {
    Write-Host "正在计算大小（可能需要几分钟）..." -ForegroundColor Yellow
    try {
        $size = (Get-ChildItem $condaBasePath -Recurse -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum / 1GB
        $sizeRounded = [math]::Round($size, 2)
        Write-Host "当前 miniconda3 占用空间: $sizeRounded GB" -ForegroundColor Cyan
        Write-Host "迁移到 D 盘后将释放 C 盘空间: $sizeRounded GB" -ForegroundColor Yellow
    } catch {
        Write-Host "无法计算大小，跳过" -ForegroundColor Yellow
    }
}
Write-Host ""

# ============================================================
# 生成迁移说明文档
# ============================================================
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

访问清华镜像（推荐，速度快）:
https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/

下载: Miniconda3-latest-Windows-x86_64.exe

### 2. 安装到 D 盘

运行安装程序，重要设置:
- 安装路径: D:\miniconda3
- 勾选 "Add Miniconda3 to my PATH environment variable"
- 勾选 "Register Miniconda3 as my default Python"

### 3. 验证新安装

关闭所有 PowerShell 窗口，重新打开:

```powershell
conda info --base
# 应该显示: D:\miniconda3
```

### 4. 恢复所有环境

进入备份目录:

```powershell
cd $backupDir
```

恢复每个环境:

$($envs | ForEach-Object { @"
# 恢复 $_ 环境
conda env create -f $_.yml

"@ })

### 5. 验证环境

```powershell
# 查看所有环境
conda env list

# 测试环境
$($envs | ForEach-Object { @"
conda activate $_
python --version
conda deactivate

"@ })
```

### 6. 删除旧的 miniconda3

只有在确认所有环境都正常后才执行:

```powershell
Remove-Item -Recurse -Force $condaBasePath
```

## 文件说明

$($envs | ForEach-Object { @"
- $_.yml - $_ 环境的完整配置
- $_.requirements.txt - $_ 环境的 pip 包列表

"@ })

## 常见问题

### PyTorch CUDA 版本

对于需要 CUDA 的环境（如 news-qwen），在恢复后需要重新安装 PyTorch:

```powershell
conda activate news-qwen
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 环境创建失败

尝试手动创建:

```powershell
conda create -n <环境名> python=3.11 -y
conda activate <环境名>
pip install -r <环境名>-requirements.txt
```

### 配置国内镜像

```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
```

"@

$readmePath = Join-Path $backupDir "README.md"
$readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
Write-Host "迁移说明已保存到: $readmePath" -ForegroundColor Green
Write-Host ""

# ============================================================
# 完成
# ============================================================
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "环境导出完成!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 查看备份目录: $backupDir" -ForegroundColor Cyan
Write-Host "2. 阅读 README.md 了解详细步骤" -ForegroundColor Cyan
Write-Host "3. 下载 Miniconda 安装程序" -ForegroundColor Cyan
Write-Host "4. 安装到 D:\miniconda3" -ForegroundColor Cyan
Write-Host "5. 使用备份的 yml 文件恢复环境" -ForegroundColor Cyan
Write-Host ""
Write-Host "Miniconda 下载地址:" -ForegroundColor Yellow
Write-Host "  清华镜像: https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/" -ForegroundColor Cyan
Write-Host "  官方地址: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Cyan
Write-Host ""

# 询问是否打开备份目录
$openDir = Read-Host "是否打开备份目录? (y/n)"
if ($openDir -eq "y") {
    explorer $backupDir
}

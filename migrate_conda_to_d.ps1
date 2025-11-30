# ============================================================
# Conda 环境迁移脚本 (C盘 -> D盘)
# 适用于 Windows PowerShell
# ============================================================

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Conda 环境迁移工具 (C盘 -> D盘)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# 检查是否在 base 环境
$currentEnv = $env:CONDA_DEFAULT_ENV
if ($currentEnv -ne "base" -and $currentEnv -ne $null) {
    Write-Host "⚠️  警告: 当前在环境 '$currentEnv' 中" -ForegroundColor Yellow
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
Write-Host "-" * 60
conda env list
Write-Host ""

# ============================================================
# 步骤 2: 创建备份目录
# ============================================================
$backupDir = "D:\conda_migration_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "步骤 2: 创建备份目录" -ForegroundColor Green
Write-Host "备份位置: $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "✓ 备份目录创建成功" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 3: 导出所有环境配置
# ============================================================
Write-Host "步骤 3: 导出所有环境配置" -ForegroundColor Green
Write-Host "-" * 60

# 获取所有环境名称（排除 base）
$envs = conda env list | Select-String -Pattern '^\w+' | ForEach-Object {
    $line = $_.Line
    if ($line -notmatch '^\s*#' -and $line -match '^(\S+)') {
        $envName = $matches[1]
        if ($envName -ne "base") {
            $envName
        }
    }
}

foreach ($env in $envs) {
    Write-Host "正在导出环境: $env" -ForegroundColor Cyan

    # 激活环境并导出
    conda activate $env

    # 导出为 yml 文件
    $ymlFile = Join-Path $backupDir "$env.yml"
    conda env export > $ymlFile
    Write-Host "  ✓ 导出到: $ymlFile" -ForegroundColor Green

    # 导出为 requirements.txt（备用）
    $reqFile = Join-Path $backupDir "$env-requirements.txt"
    pip freeze > $reqFile 2>$null
    Write-Host "  ✓ pip 包列表: $reqFile" -ForegroundColor Green

    conda deactivate
}

Write-Host ""
Write-Host "✓ 所有环境配置已导出到: $backupDir" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 4: 记录当前配置
# ============================================================
Write-Host "步骤 4: 备份 Conda 配置" -ForegroundColor Green
Write-Host "-" * 60

# 备份 .condarc
if (Test-Path "$env:USERPROFILE\.condarc") {
    Copy-Item "$env:USERPROFILE\.condarc" "$backupDir\.condarc" -Force
    Write-Host "✓ .condarc 已备份" -ForegroundColor Green
}

# 记录当前 miniconda 位置
conda info --base > "$backupDir\conda_info.txt"
Write-Host "✓ Conda 信息已保存" -ForegroundColor Green
Write-Host ""

# ============================================================
# 步骤 5: 计算空间占用
# ============================================================
Write-Host "步骤 5: 计算当前空间占用" -ForegroundColor Green
Write-Host "-" * 60

$condaPath = conda info --base | Out-String
$condaPath = $condaPath.Trim()

if (Test-Path $condaPath) {
    $size = (Get-ChildItem $condaPath -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "当前 miniconda3 占用空间: $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
    Write-Host "迁移到 D 盘后将释放 C 盘空间: $([math]::Round($size, 2)) GB" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================
# 生成迁移说明文档
# ============================================================
$readmeContent = @"
# Conda 环境迁移说明

## 备份信息
- 备份时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- 原始位置: $condaPath
- 目标位置: D:\miniconda3

## 已导出的环境

$($envs | ForEach-Object { "- $_" } | Out-String)

## 恢复步骤

### 1. 下载并安装 Miniconda 到 D 盘

访问: https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/
下载: Miniconda3-latest-Windows-x86_64.exe

**重要**: 安装路径选择 D:\miniconda3

### 2. 验证新安装

```powershell
# 关闭所有 PowerShell 窗口后重新打开
conda info --base
# 应该显示: D:\miniconda3
```

### 3. 恢复所有环境

```powershell
# 进入备份目录
cd $backupDir

# 恢复每个环境（逐个执行）
$($envs | ForEach-Object { "conda env create -f $_.yml" } | Out-String)
```

### 4. 验证环境

```powershell
# 查看所有环境
conda env list

# 测试每个环境
$($envs | ForEach-Object { @"
conda activate $_
python --version
conda deactivate
"@ } | Out-String)
```

### 5. 删除旧的 miniconda3（确认无误后）

```powershell
# ⚠️ 重要: 只有在确认所有环境都正常后才执行！
Remove-Item -Recurse -Force $condaPath
```

## 文件说明

$($envs | ForEach-Object { @"
- $_.yml - $_环境的完整配置（推荐使用）
- $_.requirements.txt - $_环境的 pip 包列表（备用）
"@ } | Out-String)

- .condarc - Conda 配置文件
- conda_info.txt - 原始 Conda 信息

## 故障排除

### 问题1: 环境创建失败

尝试手动创建环境并安装依赖:
```powershell
conda create -n <环境名> python=3.11 -y
conda activate <环境名>
pip install -r <环境名>-requirements.txt
```

### 问题2: CUDA 版本问题

PyTorch 需要单独安装:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 问题3: 某些包无法安装

检查是否需要配置国内镜像源:
```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
```

"@

$readmeContent | Out-File -FilePath "$backupDir\README.md" -Encoding UTF8
Write-Host "✓ 迁移说明已保存到: $backupDir\README.md" -ForegroundColor Green
Write-Host ""

# ============================================================
# 完成
# ============================================================
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "✓ 环境导出完成！" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
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
$open = Read-Host "是否打开备份目录? (y/n)"
if ($open -eq "y") {
    explorer $backupDir
}

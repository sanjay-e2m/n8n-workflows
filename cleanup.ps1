# N8N Workflows - Python-Only Cleanup Script for Windows
# This script removes all Node.js files and keeps only Python-related files

Write-Host "🧹 Starting N8N Workflows Python-Only Cleanup..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Remove Node.js source files
Write-Host "📁 Removing Node.js source files..." -ForegroundColor Yellow
if (Test-Path "src\") {
    Remove-Item -Recurse -Force src\
    Write-Host "   ✅ Removed src/ directory" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  src/ directory not found" -ForegroundColor Yellow
}

# Remove Node.js configuration files
Write-Host "📄 Removing Node.js configuration files..." -ForegroundColor Yellow
$nodeFiles = @("package.json", "start-nodejs.sh", "README-nodejs.md", "static\index-nodejs.html")
foreach ($file in $nodeFiles) {
    if (Test-Path $file) {
        Remove-Item -Force $file
        Write-Host "   ✅ Removed $file" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $file not found" -ForegroundColor Yellow
    }
}

# Remove Python cache files
Write-Host "🐍 Removing Python cache files..." -ForegroundColor Yellow
if (Test-Path "__pycache__\") {
    Remove-Item -Recurse -Force __pycache__\
    Write-Host "   ✅ Removed __pycache__/ directory" -ForegroundColor Green
}

# Remove compiled Python files
$pycFiles = Get-ChildItem -Recurse -Name "*.pyc" -ErrorAction SilentlyContinue
if ($pycFiles) {
    $pycFiles | Remove-Item -Force
    Write-Host "   ✅ Removed $($pycFiles.Count) .pyc files" -ForegroundColor Green
}

$pyoFiles = Get-ChildItem -Recurse -Name "*.pyo" -ErrorAction SilentlyContinue
if ($pyoFiles) {
    $pyoFiles | Remove-Item -Force
    Write-Host "   ✅ Removed $($pyoFiles.Count) .pyo files" -ForegroundColor Green
}

# Remove virtual environment (optional)
Write-Host "🔧 Virtual environment cleanup..." -ForegroundColor Yellow
if (Test-Path "venv\") {
    $response = Read-Host "   Remove virtual environment? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item -Recurse -Force venv\
        Write-Host "   ✅ Removed venv/ directory" -ForegroundColor Green
    } else {
        Write-Host "   ⏭️  Keeping venv/ directory" -ForegroundColor Yellow
    }
}

# Remove database files
Write-Host "🗄️ Removing database files..." -ForegroundColor Yellow
$dbFiles = Get-ChildItem -Recurse -Name "database\workflows.db*" -ErrorAction SilentlyContinue
if ($dbFiles) {
    $dbFiles | Remove-Item -Force
    Write-Host "   ✅ Removed database files (will be regenerated)" -ForegroundColor Green
}

# Remove other database files
$otherDbFiles = Get-ChildItem -Recurse -Name "*.db", "*.sqlite", "*.sqlite3" -ErrorAction SilentlyContinue
if ($otherDbFiles) {
    $otherDbFiles | Remove-Item -Force
    Write-Host "   ✅ Removed $($otherDbFiles.Count) database files" -ForegroundColor Green
}

# Remove temporary files
Write-Host "🗑️ Removing temporary files..." -ForegroundColor Yellow
$tempExtensions = @("*.log", "*.tmp", "*.temp", "*.bak", "*.backup")
foreach ($ext in $tempExtensions) {
    $files = Get-ChildItem -Recurse -Name $ext -ErrorAction SilentlyContinue
    if ($files) {
        $files | Remove-Item -Force
        Write-Host "   ✅ Removed $($files.Count) $ext files" -ForegroundColor Green
    }
}

# Remove IDE files
Write-Host "💻 Removing IDE files..." -ForegroundColor Yellow
$ideDirs = @(".vscode", ".idea")
foreach ($dir in $ideDirs) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "   ✅ Removed $dir/ directory" -ForegroundColor Green
    }
}

# Remove editor swap files
$swapFiles = Get-ChildItem -Recurse -Name "*.swp", "*.swo", "*~" -ErrorAction SilentlyContinue
if ($swapFiles) {
    $swapFiles | Remove-Item -Force
    Write-Host "   ✅ Removed $($swapFiles.Count) editor swap files" -ForegroundColor Green
}

# Remove OS files
Write-Host "🖥️ Removing OS files..." -ForegroundColor Yellow
$osFiles = Get-ChildItem -Recurse -Name ".DS_Store", "Thumbs.db" -ErrorAction SilentlyContinue
if ($osFiles) {
    $osFiles | Remove-Item -Force
    Write-Host "   ✅ Removed $($osFiles.Count) OS files" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Cleanup completed!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Your project now contains only Python-related files." -ForegroundColor Cyan
Write-Host "You can now run: python run.py" -ForegroundColor Cyan
Write-Host ""

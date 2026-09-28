[CmdletBinding()]
param(
    [string]$Python = "",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ToolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ToolDir "..\..")).Path
Set-Location $RepoRoot

function Resolve-BuildPython {
    param([string]$Explicit)

    $candidates = @()
    if ($Explicit) { $candidates += $Explicit }
    if ($env:DUDEDABBLER_PORTABLE_BUILD_PYTHON) { $candidates += $env:DUDEDABBLER_PORTABLE_BUILD_PYTHON }
    if ($env:IFOAM_PORTABLE_BUILD_PYTHON) { $candidates += $env:IFOAM_PORTABLE_BUILD_PYTHON }

    try {
        $fromLauncher = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
        if ($fromLauncher) { $candidates += $fromLauncher.Trim() }
    } catch {}

    $known = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        "C:\Python312\python.exe"
    )
    $candidates += $known

    try {
        $command = Get-Command python -ErrorAction Stop
        $candidates += $command.Source
    } catch {}

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path $candidate).Path
        }
    }
    throw "Python 3.12 x64 не найден. Укажите путь через -Python или DUDEDABBLER_PORTABLE_BUILD_PYTHON."
}

function Invoke-Checked {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments
    )
    Write-Host "[$Label] $FilePath $($Arguments -join ' ')"
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label завершился с кодом $LASTEXITCODE."
    }
}

$branch = (git branch --show-current).Trim()
$commit = (git rev-parse HEAD).Trim()
$upstream = ""
try { $upstream = (git rev-parse "@{u}" 2>$null).Trim() } catch {}
$status = git status --porcelain
if ($status) {
    throw "Рабочее дерево не чистое. Сначала зафиксируйте или отмените изменения:`n$status"
}
if ($upstream -and $upstream -ne $commit) {
    throw "Локальный HEAD $commit не совпадает с upstream $upstream. Выполните git pull --ff-only."
}

$pythonExe = Resolve-BuildPython -Explicit $Python
$bits = (& $pythonExe -c "import struct; print(struct.calcsize('P') * 8)").Trim()
$pyVersion = (& $pythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
if ($bits -ne "64") {
    throw "Для portable win-x64 нужен 64-битный Python. Найдено: $bits-bit."
}

$version = (& $pythonExe -c "from tools.ozon_price_exporter import __version__; print(__version__)").Trim()
$venvDir = Join-Path $RepoRoot "build\ozon_price_exporter_portable_venv"
$workDir = Join-Path $RepoRoot "build\ozon_price_exporter_portable"
$distRoot = Join-Path $RepoRoot "dist\ozon_price_exporter_portable"
$bundleDir = Join-Path $distRoot "OzonPriceExporter"
$exePath = Join-Path $bundleDir "OzonPriceExporter.exe"
$zipPath = Join-Path $RepoRoot "dist\OzonPriceExporter-$version-win-x64.zip"
$shaPath = "$zipPath.sha256"

Write-Host "============================================================"
Write-Host " Ozon Customer Price Exporter portable build"
Write-Host " version=$version"
Write-Host " branch=$branch"
Write-Host " commit=$commit"
Write-Host " python=$pyVersion ($bits-bit)"
Write-Host "============================================================"

Remove-Item $venvDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $workDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $distRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Remove-Item $shaPath -Force -ErrorAction SilentlyContinue

Invoke-Checked "venv" $pythonExe @("-m", "venv", $venvDir)
$buildPython = Join-Path $venvDir "Scripts\python.exe"
Invoke-Checked "pip-upgrade" $buildPython @("-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip")
Invoke-Checked "build-deps" $buildPython @(
    "-m", "pip", "install", "--disable-pip-version-check",
    "-r", (Join-Path $ToolDir "portable_build_requirements.txt")
)

if (-not $SkipTests) {
    Invoke-Checked "tests" $buildPython @(
        "-m", "pytest", "-q",
        "tests\test_ozon_price_exporter.py",
        "tests\test_ozon_price_exporter_portable.py"
    )
}

Invoke-Checked "pyinstaller" $buildPython @(
    "-m", "PyInstaller",
    (Join-Path $ToolDir "ozon_price_exporter_portable.spec"),
    "--clean",
    "--noconfirm",
    "--distpath", $distRoot,
    "--workpath", $workDir
)

if (-not (Test-Path $exePath)) {
    throw "PyInstaller не создал ожидаемый EXE: $exePath"
}

Copy-Item (Join-Path $ToolDir "PORTABLE_README.txt") (Join-Path $bundleDir "README.txt") -Force

$depsJson = & $buildPython -c @"
import importlib.metadata as m, json
print(json.dumps({
    "playwright": m.version("playwright"),
    "openpyxl": m.version("openpyxl"),
    "pyinstaller": m.version("pyinstaller")
}))
"@
$deps = $depsJson | ConvertFrom-Json
$manifest = [ordered]@{
    product = "Ozon Customer Price Exporter"
    publisher = "DudeDabbler"
    repository = "DudeDabbler/OzonPriceExporter"
    version = $version
    distribution = "portable-onedir"
    target = "windows-x64"
    branch = $branch
    commit = $commit
    built_at = (Get-Date).ToString("o")
    build_python = $pyVersion
    dependencies = [ordered]@{
        playwright = $deps.playwright
        openpyxl = $deps.openpyxl
        pyinstaller = $deps.pyinstaller
    }
    runtime_requirements = @("Windows x64", "Google Chrome or Microsoft Edge")
    marketplace_writes = 0
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    (Join-Path $bundleDir "BUILD_MANIFEST.json"),
    ($manifest | ConvertTo-Json -Depth 5),
    $utf8NoBom
)

Invoke-Checked "portable-smoke" $buildPython @(
    (Join-Path $ToolDir "portable_smoke.py"),
    $exePath,
    "--expected-version", $version
)

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $bundleDir,
    $zipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)

$hash = (Get-FileHash -Algorithm SHA256 $zipPath).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText(
    $shaPath,
    "$hash *$(Split-Path $zipPath -Leaf)`r`n",
    $utf8NoBom
)

$zipMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "PORTABLE_BUILD_PASS"
Write-Host "Folder: $bundleDir"
Write-Host "ZIP:    $zipPath ($zipMb MB)"
Write-Host "SHA256: $hash"

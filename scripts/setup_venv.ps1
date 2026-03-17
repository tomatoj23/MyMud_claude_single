param(
    [switch]$InstallDev
)

$ErrorActionPreference = "Stop"

$preferredVersions = @("-3.13", "-3.12", "-3.11")
$selectedVersion = $null
$hasPython314 = $false

foreach ($version in $preferredVersions) {
    cmd /c "py $version -c \"import sys\" >nul 2>nul"
    if ($LASTEXITCODE -eq 0) {
        $selectedVersion = $version
        break
    }
}

cmd /c "py -3.14 -c ""import sys"" >nul 2>nul"
if ($LASTEXITCODE -eq 0) {
    $hasPython314 = $true
}

if (-not $selectedVersion) {
    if ($hasPython314) {
        Write-Warning "Python 3.14 is installed and may work in an existing local setup, but this script intentionally prefers Python 3.13/3.12/3.11 for reproducible project environments because qasync does not officially declare Python 3.14 support yet."
    }
    Write-Error "No recommended Python interpreter found. Install Python 3.13 (recommended) or 3.12/3.11, then rerun this script."
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$venvPath = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv with $selectedVersion ..."
    & py $selectedVersion -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment with $selectedVersion"
    }
}

$resolvedPython = (Resolve-Path $venvPython).Path
Write-Host "Using virtual environment interpreter: $resolvedPython"

& $resolvedPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip tooling inside .venv"
}

if ($InstallDev) {
    Push-Location $projectRoot
    try {
        & $resolvedPython -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install project dependencies into .venv"
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "Virtual environment is ready. Activate it with .\.venv\Scripts\Activate.ps1"
    Write-Host 'Then install dependencies with: python -m pip install -e ".[dev]"'
}

param(
    [int]$Workers = 5,
    [string]$ResultsDirectory = "allure-results-api"
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtual-environment Python was not found at $Python"
}

Push-Location $RepositoryRoot
try {
    Write-Host "Phase 1/2: parallel API tests ($Workers workers)"
    & $Python -m pytest `
        -n $Workers `
        -m "api and not serial" `
        -q `
        --alluredir=$ResultsDirectory `
        --clean-alluredir
    $ParallelExitCode = $LASTEXITCODE

    Write-Host "Phase 2/2: serial API tests (one worker)"
    & $Python -m pytest `
        -n 0 `
        -m "api and serial" `
        -q `
        --alluredir=$ResultsDirectory
    $SerialExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($ParallelExitCode -ne 0 -or $SerialExitCode -ne 0) {
    exit 1
}

exit 0

param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,
    [string]$ProjectId = "steel_ingot_pilot",
    [string]$StorePath = ".nexus/runtime/expert_foundry",
    [string]$PythonPath,
    [switch]$Commit
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = if ($PythonPath) { (Resolve-Path -LiteralPath $PythonPath).Path } else { Join-Path $repoRoot ".venv\Scripts\python.exe" }
$inputPath = (Resolve-Path -LiteralPath $InputFile).Path
$storeFullPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $StorePath))

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Project Python was not found at $pythonPath. Create the project .venv or pass -PythonPath. Do not use bare python."
}

$arguments = @(
    (Join-Path $repoRoot "foundry_ingestion.py"),
    "--input", $inputPath,
    "--project-id", $ProjectId,
    "--store", $storeFullPath
)

if (-not $Commit) {
    $arguments += "--dry-run"
    Write-Host "PREVIEW ONLY: no evidence will be stored."
} else {
    Write-Host "COMMIT MODE: accepted records and the immutable raw file will be stored."
}

& $pythonPath @arguments
exit $LASTEXITCODE

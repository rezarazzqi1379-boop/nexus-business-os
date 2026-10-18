param(
    [Parameter(Mandatory = $true)] [string]$PythonPath,
    [Parameter(Mandatory = $true)] [string[]]$SkillRoots
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = (Resolve-Path -LiteralPath $PythonPath).Path
$arguments = @((Join-Path $repoRoot 'maintenance_preflight.py'), '--repo', $repoRoot)
foreach ($skillRoot in $SkillRoots) { $arguments += @('--skill-root', $skillRoot) }
# Fixed Python entry point and argv; no Invoke-Expression, installs or external writes.
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "Maintenance preflight failed: exit $LASTEXITCODE" }

# Wrapper script: delegates to run_local_test.ps1
#
# This script maintains backward compatibility with existing workflows.
# All logic is centralized in run_local_test.ps1 to avoid duplication.

param(
    [string]$DistroName = "Ubuntu",
    [switch]$SkipBenchmark,
    [switch]$SkipReport,
    [int]$MaxTokens = 0
)

$ErrorActionPreference = "Stop"

# Navigate to project root
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

# Delegate to main test script
$argsList = @(
    "-DistroName", $DistroName,
    "-SkipBenchmark:$SkipBenchmark",
    "-SkipReport:$SkipReport"
)

if ($MaxTokens -gt 0) {
    $argsList += @("-MaxTokens", $MaxTokens)
}

& ".\run_local_test.ps1" @argsList

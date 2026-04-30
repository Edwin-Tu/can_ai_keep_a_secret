# Wrapper script: delegates to run_local_test.ps1
# 
# This script maintains backward compatibility with existing workflows.
# All logic is centralized in run_local_test.ps1 to avoid duplication.

param(
    [string]$DistroName = "Ubuntu",
    [switch]$SkipBenchmark,
    [switch]$SkipReport,
    [int]$MaxTokens = 800
)

$ErrorActionPreference = "Stop"

# Navigate to project root
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

# Delegate to main test script
& ".\run_local_test.ps1" `
    -DistroName $DistroName `
    -SkipBenchmark:$SkipBenchmark `
    -SkipReport:$SkipReport `
    -MaxTokens $MaxTokens
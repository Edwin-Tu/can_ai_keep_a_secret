# Wrapper script: delegates to run_local_test.ps1
#
# This script maintains backward compatibility with existing workflows.
# All benchmark/report logic is centralized in run_local_test.ps1 to avoid duplication.

param(
    [string]$DistroName = "Ubuntu",
    [switch]$SkipBenchmark,
    [switch]$SkipReport,
    [int]$MaxTokens = 800,
    [switch]$Unlimited,
    [double]$Temperature = 0,
    [ValidateSet("public", "internal")]
    [string]$ReportMode = "public"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$argsList = @(
    "-DistroName", $DistroName,
    "-Temperature", $Temperature,
    "-ReportMode", $ReportMode
)

if ($SkipBenchmark) { $argsList += "-SkipBenchmark" }
if ($SkipReport) { $argsList += "-SkipReport" }

if ($Unlimited) {
    $argsList += "-Unlimited"
}
else {
    $argsList += @("-MaxTokens", $MaxTokens)
}

& ".\run_local_test.ps1" @argsList

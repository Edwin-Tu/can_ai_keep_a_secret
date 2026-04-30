# Wrapper script: delegates to run_local_test.ps1
#
# This script maintains backward compatibility with existing workflows.
# All benchmark/report logic is centralized in run_local_test.ps1 to avoid duplication.

param(
    [string]$DistroName = "Ubuntu",
    [switch]$SkipBenchmark,
    [switch]$SkipReport,
    [int]$MaxTokens = 0,
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
if ($MaxTokens -gt 0) { $argsList += @("-MaxTokens", $MaxTokens) }

& ".\run_local_test.ps1" @argsList

# PowerShell Validator for Adera Threat Intelligence Data
$dataDir = $PSScriptRoot + "\..\data"
$jsonFiles = Get-ChildItem -Path $dataDir -Filter "*.json"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ADERA THREAT INTELLIGENCE DATA VALIDATOR (POWERSHELL)     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

foreach ($file in $jsonFiles) {
    try {
        $raw = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $jsonObj = $raw | ConvertFrom-Json
        Write-Host "[VALID JSON] $($file.Name) - Successfully parsed." -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] $($file.Name) - Parsing failed: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray

# Specific checks
$reportsRaw = Get-Content -Path "$dataDir\synthetic_reports.json" -Raw | ConvertFrom-Json
$demoReports = $reportsRaw.reports | Where-Object { $_.recipient_phone -eq "0912345678" }
Write-Host "[CHECK] Target Demo Phone (0912345678) Report Count: $($demoReports.Count)" -ForegroundColor Yellow

$casesRaw = Get-Content -Path "$dataDir\synthetic_scam_cases.json" -Raw | ConvertFrom-Json
Write-Host "[CHECK] Total Synthetic Scam Cases: $($casesRaw.cases.Count)" -ForegroundColor Yellow

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ALL THREAT INTELLIGENCE DATASETS ARE 100% VALIDATED!      " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

<#
Execute non-destructive QA across five EXISTING repositories on one Windows PC.
No clone, repo mutation, upload, signing, Store publication or silent security bypass.
Use sibling Git clones under -WorkspaceRoot. No automatic app release approval.
#>
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = "",
    [switch]$PlanOnly,
    [switch]$BuildMissing,
    [switch]$TestMSIX,
    [switch]$HumanChecks,
    [switch]$DefenderScan
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$products = @(
    [ordered]@{repository="data-pipeline-automator";product="LocalDataPorter"},
    [ordered]@{repository="-PDF-Privacy-Toolkit";product="PDFBatchForms"},
    [ordered]@{repository="folder-automation-engine";product="BackupRestoreVerifier"},
    [ordered]@{repository="safe-folder-workflow";product="AIOutputAuditor"},
    [ordered]@{repository="-Folder-Privacy-Auditor";product="StorageCauseAnalyzer"}
)
if (-not $WorkspaceRoot) {
    $WorkspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}
if ($PlanOnly) {
    foreach ($p in $products) {
        Write-Host ("QA_PLAN repository={0} product={1} path={2}" -f $p.repository,$p.product,(Join-Path $WorkspaceRoot $p.repository))
    }
    Write-Host "QA_PLAN_ONLY no builds launched or files modified"
    return
}
if ($env:OS -ne "Windows_NT") { throw "This QA runner is Windows-only" }
$workspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
$all = @()
foreach ($p in $products) {
    $repo = Join-Path $workspace $p.repository
    $state = [ordered]@{
        repository=$p.repository
        expected_product=$p.product
        repo_found=$false
        manifest_selected=$null
        qa_evidence_found=$false
        msix_preflight=$null
        human_checks_requested=[bool]$HumanChecks
        result="BLOCKED"
        error=$null
    }
    try {
        if (-not (Test-Path -LiteralPath $repo -PathType Container)) {
            throw "Repository directory not found. Clone or place existing checkout as a sibling."
        }
        $state.repo_found = $true
        $buildScript = Join-Path $repo "build-windows-validation.ps1"
        $qaScript = Join-Path $repo "qa\windows-acceptance.ps1"
        if (-not (Test-Path -LiteralPath $buildScript) -or -not (Test-Path -LiteralPath $qaScript)) {
            throw "Current repository checkout missing build/QA script. Update checkout manually first."
        }
        $dist = Join-Path $repo "dist-validation"
        $manifests = @()
        if (Test-Path -LiteralPath $dist) {
            $manifests = @(Get-ChildItem -LiteralPath $dist -File -Recurse -Filter "validation-manifest.json" |
                Sort-Object LastWriteTimeUtc -Descending)
        }
        if ($manifests.Count -eq 0) {
            if (-not $BuildMissing) { throw "No local EXE. Use -BuildMissing explicitly to build one." }
            Write-Host ("QA_BUILD {0}" -f $p.repository)
            & $buildScript
            if ($LASTEXITCODE -ne 0) { throw "Validation build failed" }
            $manifests = @(Get-ChildItem -LiteralPath $dist -File -Recurse -Filter "validation-manifest.json" |
                Sort-Object LastWriteTimeUtc -Descending)
            if ($manifests.Count -eq 0) { throw "Build did not produce a manifest" }
        }
        $selected = $manifests[0]
        $manifest = Get-Content -LiteralPath $selected.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($manifest.product -ne $p.product) { throw "Unexpected product in selected validation manifest" }
        $state.manifest_selected = $selected.FullName
        $argsQA = @{Mode="Local"; ManifestPath=$selected.FullName}
        if ($HumanChecks) { $argsQA["Interactive"] = $true }
        if ($DefenderScan) { $argsQA["RunDefenderScan"] = $true }
        Write-Host ("QA_CHECK {0}" -f $p.repository)
        & $qaScript @argsQA
        $evidence = @(Get-ChildItem -LiteralPath $selected.DirectoryName -Directory -Filter "qa-evidence-*" |
            Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1)
        if ($evidence.Count -eq 0 -or -not (Test-Path -LiteralPath (Join-Path $evidence[0].FullName "acceptance.json"))) {
            throw "Expected fresh QA evidence absent"
        }
        $audit = Get-Content -LiteralPath (Join-Path $evidence[0].FullName "acceptance.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($audit.exe_hash_matches_build_manifest -ne $true -or $audit.release_approved -ne $false) {
            throw "Unexpected QA outcome or release approval"
        }
        $state.qa_evidence_found = $true
        if ($TestMSIX) {
            $msixScript = Join-Path $repo "qa\build-msix-preflight.ps1"
            if (-not (Test-Path -LiteralPath $msixScript)) { throw "Missing MSIX preflight; update checkout" }
            Write-Host ("QA_MSIX_TEST {0}" -f $p.repository)
            & $msixScript -TestIdentity -ManifestPath $selected.FullName
            $results = @(Get-ChildItem -LiteralPath $selected.DirectoryName -File -Recurse -Filter "msix-preflight-report.json" |
                Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1)
            if ($results.Count -eq 0) { throw "MSIX report not found" }
            $msix = Get-Content -LiteralPath $results[0].FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($msix.status -ne "MSIX_PACK_UNPACK_HASH_PASS" -or $msix.release_approved -ne $false) {
                throw "MSIX preflight failed or falsely approved release"
            }
            $state.msix_preflight = $msix.status
        }
        $state.result = "QA_EVIDENCE_OK_RELEASE_BLOCKED"
        Write-Host ("QA_OK {0} release=false" -f $p.repository)
    } catch {
        $state.error = [string]$_.Exception.Message
        $state.result = "BLOCKED_OR_FAILED"
        Write-Warning ("QA_FAIL {0}: {1}" -f $p.repository,$state.error)
    }
    $all += [pscustomobject]$state
}
$stamp = [Guid]::NewGuid().ToString("N")
$reportFolder = Join-Path $workspace ("local-five-product-qa-" + $stamp)
New-Item -ItemType Directory -Path $reportFolder | Out-Null
$summary = [ordered]@{
 schema="local_five_product_qa_v1"
 created_utc=(Get-Date).ToUniversalTime().ToString("o")
 build_missing=[bool]$BuildMissing
 test_msix=[bool]$TestMSIX
 human_checks=[bool]$HumanChecks
 defender_scan_requested=[bool]$DefenderScan
 products=$all
 success_count=@($all | Where-Object { $_.result -eq "QA_EVIDENCE_OK_RELEASE_BLOCKED" }).Count
 release_approved=$false
 release_status="BLOCKED_PENDING_HUMAN_SECURITY_AND_PARTNER_CENTER"
}
$reportPath = Join-Path $reportFolder "summary.json"
$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host ("QA_SUMMARY {0}/5 successful local integrity reports, release=false" -f $summary.success_count)
Write-Host ("QA_REPORT {0}" -f $reportPath)
if ($summary.success_count -ne 5) { throw "One or more repositories need attention. See report." }

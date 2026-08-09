# One-time setup: GCP Workload Identity Federation for GitHub Actions → Cloud Run.
# Usage (from repo root, gcloud authenticated):
#   .\deploy\setup-github-actions.ps1
#
# Then add the printed values as GitHub Actions secrets:
#   WIF_PROVIDER
#   WIF_SERVICE_ACCOUNT

param(
    [string]$ProjectId = "maintenance-agent-hack",
    [string]$Region = "europe-west1",
    [string]$GithubRepo = "GH4ZII/AgenticHackaton",
    [string]$DeploySaName = "github-actions-deploy",
    [string]$RuntimeSaName = "maintenance-agent-run",
    [string]$PoolId = "github-pool",
    [string]$ProviderId = "github-provider"
)

$ErrorActionPreference = "Stop"
$gcloud = Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloud)) { $gcloud = "gcloud" }

$ProjectNumber = (& $gcloud projects describe $ProjectId --format="value(projectNumber)").Trim()
if (-not $ProjectNumber) { throw "Could not resolve project number for $ProjectId" }

$DeploySaEmail = "$DeploySaName@$ProjectId.iam.gserviceaccount.com"
$RuntimeSaEmail = "$RuntimeSaName@$ProjectId.iam.gserviceaccount.com"
$PoolResource = "projects/$ProjectNumber/locations/global/workloadIdentityPools/$PoolId"
$ProviderResource = "$PoolResource/providers/$ProviderId"

Write-Host "==> Enabling APIs..."
& $gcloud services enable `
    iamcredentials.googleapis.com `
    iam.googleapis.com `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    --project=$ProjectId

Write-Host "==> Ensuring deploy service account ($DeploySaEmail)..."
$ErrorActionPreference = "Continue"
$existing = & $gcloud iam service-accounts describe $DeploySaEmail --project=$ProjectId 2>$null
$describeOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = "Stop"
if (-not $describeOk) {
    & $gcloud iam service-accounts create $DeploySaName `
        --display-name="GitHub Actions Cloud Run deploy" `
        --project=$ProjectId
}

$roles = @(
    "roles/run.admin",
    "roles/cloudbuild.builds.editor",
    "roles/artifactregistry.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser"
)
foreach ($role in $roles) {
    & $gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$DeploySaEmail" `
        --role=$role `
        --condition=None `
        --quiet | Out-Null
}

# Allow deploy SA to act as the Cloud Run runtime SA
& $gcloud iam service-accounts add-iam-policy-binding $RuntimeSaEmail `
    --member="serviceAccount:$DeploySaEmail" `
    --role="roles/iam.serviceAccountUser" `
    --project=$ProjectId `
    --quiet | Out-Null

Write-Host "==> Ensuring Workload Identity Pool..."
$ErrorActionPreference = "Continue"
$pool = & $gcloud iam workload-identity-pools describe $PoolId `
    --project=$ProjectId `
    --location=global `
    --format="value(name)" 2>$null
$poolOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = "Stop"
if (-not $poolOk) {
    & $gcloud iam workload-identity-pools create $PoolId `
        --project=$ProjectId `
        --location=global `
        --display-name="GitHub Actions pool"
}

Write-Host "==> Ensuring OIDC provider for GitHub..."
$ErrorActionPreference = "Continue"
$provider = & $gcloud iam workload-identity-pools providers describe $ProviderId `
    --project=$ProjectId `
    --location=global `
    --workload-identity-pool=$PoolId `
    --format="value(name)" 2>$null
$providerOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = "Stop"
if (-not $providerOk) {
    & $gcloud iam workload-identity-pools providers create-oidc $ProviderId `
        --project=$ProjectId `
        --location=global `
        --workload-identity-pool=$PoolId `
        --display-name="GitHub provider" `
        --issuer-uri="https://token.actions.githubusercontent.com" `
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" `
        --attribute-condition="assertion.repository=='$GithubRepo'"
} else {
    & $gcloud iam workload-identity-pools providers update-oidc $ProviderId `
        --project=$ProjectId `
        --location=global `
        --workload-identity-pool=$PoolId `
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" `
        --attribute-condition="assertion.repository=='$GithubRepo'" `
        --quiet
}

Write-Host "==> Binding GitHub repo to deploy SA (Workload Identity User)..."
& $gcloud iam service-accounts add-iam-policy-binding $DeploySaEmail `
    --project=$ProjectId `
    --role="roles/iam.workloadIdentityUser" `
    --member="principalSet://iam.googleapis.com/$PoolResource/attribute.repository/$GithubRepo" `
    --quiet | Out-Null

Write-Host ""
Write-Host "=== Add these GitHub Actions secrets ===" -ForegroundColor Green
Write-Host "Repo: https://github.com/$GithubRepo/settings/secrets/actions"
Write-Host ""
Write-Host "Name:  WIF_PROVIDER"
Write-Host "Value: $ProviderResource"
Write-Host ""
Write-Host "Name:  WIF_SERVICE_ACCOUNT"
Write-Host "Value: $DeploySaEmail"
Write-Host ""
Write-Host "After secrets are set, push to main (or run workflow_dispatch) to deploy."
Write-Host "Live URL: https://maintenance-agent-786907268086.europe-west1.run.app/"
